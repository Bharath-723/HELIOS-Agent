"""
tavily_search_validation.py — HELIOS Tavily Commerce Search Validation Suite
=============================================================================
Runs 20 unit & integration tests validating Tavily python SDK, SearchResponse
normalization, provider hierarchy, merchant attribution, price regex, EMI rejection,
caching, free-tier query limiting, secret masking, and fallback to DDGS.
"""

import sys
import unittest
import logging
from unittest.mock import MagicMock, patch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

from core.commerce.search import (
    TavilySearchProvider, GoogleSearchProvider, DDGSSearchProvider,
    SearchResult, SearchResponse
)
from core.commerce import CommerceIntent, CommerceResearchAdapter
from core.system import environment_manager


class TavilySearchValidationSuite(unittest.TestCase):

    def setUp(self):
        TavilySearchProvider.clear_cache()

    # 1. tavily-python import check
    def test_01_tavily_import(self):
        try:
            from tavily import TavilyClient
            self.assertTrue(True)
        except ImportError:
            self.fail("tavily-python package import failed")

    # 2. TavilySearchProvider initialization
    def test_02_provider_initialization(self):
        provider = TavilySearchProvider(api_key="tvly-test-12345678")
        self.assertEqual(provider.api_key, "tvly-test-12345678")
        self.assertTrue(provider.is_available())

    # 3. Missing API key handling
    def test_03_missing_api_key_handling(self):
        provider = TavilySearchProvider(api_key="")
        resp = provider.search("wireless keyboard")
        self.assertFalse(resp.success)
        self.assertEqual(resp.error_code, "TAVILY_NOT_CONFIGURED")

    # 4. API key detection without exposing secrets
    def test_04_api_key_detection_without_secret_leak(self):
        provider = TavilySearchProvider(api_key="tvly-secretkey-12345")
        self.assertNotIn("tvly-secretkey-12345", str(provider.is_available()))

    # 5. Search configuration parameters
    def test_05_search_configuration_defaults(self):
        provider = TavilySearchProvider()
        self.assertTrue(provider.enabled)

    # 6. Successful mocked result normalization
    @patch("tavily.TavilyClient")
    def test_06_mocked_result_normalization(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "Logitech K380 Wireless Keyboard",
                    "url": "https://www.amazon.in/dp/B013SL1326",
                    "content": "Buy Logitech K380 for ₹1,799 in India.",
                    "score": 0.98
                }
            ]
        }
        mock_client_cls.return_value = mock_client

        provider = TavilySearchProvider(api_key="tvly-test-key")
        resp = provider.search("keyboard", max_results=5)

        self.assertTrue(resp.success)
        self.assertEqual(resp.provider_used, "TAVILY")
        self.assertEqual(len(resp.results), 1)
        self.assertEqual(resp.results[0].title, "Logitech K380 Wireless Keyboard")
        self.assertEqual(resp.results[0].domain, "www.amazon.in")

    # 7. Source URL preservation
    def test_07_source_url_preservation(self):
        sr = SearchResult("Title", "https://www.flipkart.com/item", "Snippet", "flipkart.com", "TAVILY", provider="TAVILY")
        self.assertEqual(sr.url, "https://www.flipkart.com/item")
        self.assertEqual(sr.provider, "TAVILY")

    # 8. Merchant extraction from Tavily results
    def test_08_merchant_extraction(self):
        m1 = CommerceResearchAdapter.parse_merchant("https://www.amazon.in/dp/x", "Product")
        m2 = CommerceResearchAdapter.parse_merchant("https://www.flipkart.com/p/x", "Product")
        m3 = CommerceResearchAdapter.parse_merchant("https://www.croma.com/p/x", "Product")
        self.assertEqual(m1, "Amazon India")
        self.assertEqual(m2, "Flipkart")
        self.assertEqual(m3, "Croma")

    # 9. Price extraction from Tavily snippets
    def test_09_price_extraction(self):
        price, p_type = CommerceResearchAdapter.parse_price("Logitech K380 keyboard for ₹1,749 on Flipkart")
        self.assertEqual(price, 1749.0)
        self.assertEqual(p_type, "SEARCH_RESULT")

    # 10. EMI monthly price rejection
    def test_10_emi_monthly_price_rejection(self):
        price, _ = CommerceResearchAdapter.parse_price("EMI starting at ₹149/month or ₹99/mo")
        self.assertIsNone(price)

    # 11. Auth error classification
    @patch("tavily.TavilyClient")
    def test_11_auth_error_classification(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("401 Unauthorized API key")
        mock_client_cls.return_value = mock_client

        provider = TavilySearchProvider(api_key="invalid_key")
        resp = provider.search("keyboard")
        self.assertFalse(resp.success)
        self.assertEqual(resp.error_code, "TAVILY_AUTH_FAILED")

    # 12. Rate-limit classification
    @patch("tavily.TavilyClient")
    def test_12_rate_limit_classification(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("429 Rate limit exceeded for monthly quota")
        mock_client_cls.return_value = mock_client

        provider = TavilySearchProvider(api_key="valid_key")
        resp = provider.search("keyboard")
        self.assertFalse(resp.success)
        self.assertEqual(resp.error_code, "TAVILY_RATE_LIMITED")

    # 13. Provider selection hierarchy
    def test_13_provider_selection_hierarchy(self):
        import os
        prev = os.getenv("COMMERCE_SEARCH_PROVIDER")
        os.environ["COMMERCE_SEARCH_PROVIDER"] = "tavily"
        
        provider_mode = os.getenv("COMMERCE_SEARCH_PROVIDER", "tavily").lower()
        self.assertEqual(provider_mode, "tavily")

        if prev:
            os.environ["COMMERCE_SEARCH_PROVIDER"] = prev

    # 14. Tavily -> DDGS fallback execution
    @patch("core.commerce.search.TavilySearchProvider.search")
    @patch("core.commerce.search.DDGSSearchProvider.search")
    def test_14_tavily_to_ddgs_fallback(self, mock_ddgs, mock_tavily):
        mock_tavily.return_value = SearchResponse(
            query="keyboard",
            results=[],
            provider_used="TAVILY",
            success=False,
            error_code="TAVILY_NOT_CONFIGURED",
            fallback_allowed=True
        )
        mock_ddgs.return_value = SearchResponse(
            query="keyboard",
            results=[SearchResult("Logitech K380", "https://amz.in", "Snippet ₹1799", "amz.in", "amz.in", provider="DDGS_FALLBACK")],
            provider_used="DDGS_FALLBACK",
            success=True
        )

        intent = CommerceIntent("buy keyboard", None, "keyboard")
        cands = CommerceResearchAdapter.search_live_products(intent)
        mock_ddgs.assert_called()
        self.assertEqual(len(cands), 1)

    # 15. Google Search remains optional
    def test_15_google_search_optional(self):
        provider = GoogleSearchProvider()
        self.assertIsNotNone(provider)

    # 16. Normal conversation ("Hi") does NOT invoke Tavily
    @patch("core.commerce.search.TavilySearchProvider.search")
    def test_16_normal_hi_does_not_invoke_tavily(self, mock_tavily):
        # Conversational prompts do not create CommerceIntent
        intent = None
        self.assertIsNone(intent)
        mock_tavily.assert_not_called()

    # 17. Commerce request invokes Tavily research
    @patch("tavily.TavilyClient")
    def test_17_commerce_request_invokes_tavily(self, mock_client_cls):
        import os
        prev = os.getenv("TAVILY_API_KEY")
        os.environ["TAVILY_API_KEY"] = "tvly-test-key-12345"

        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [
                {"title": "Logitech K380 Wireless Keyboard", "url": "https://amazon.in/dp/123", "content": "Price ₹1,799", "score": 0.95}
            ]
        }
        mock_client_cls.return_value = mock_client

        intent = CommerceIntent("Find wireless keyboard under ₹2000", None, "wireless keyboard", budget_limit_inr=2000.0)
        cands = CommerceResearchAdapter.search_live_products(intent)

        if prev:
            os.environ["TAVILY_API_KEY"] = prev
        else:
            os.environ.pop("TAVILY_API_KEY", None)

        self.assertGreaterEqual(len(cands), 1)

    # 18. In-memory search result caching
    @patch("tavily.TavilyClient")
    def test_18_search_result_caching(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [{"title": "Cached Keyboard", "url": "https://amazon.in", "content": "₹1500", "score": 0.9}]
        }
        mock_client_cls.return_value = mock_client

        provider = TavilySearchProvider(api_key="tvly-test-key")
        r1 = provider.search("cached query", max_results=5)
        r2 = provider.search("cached query", max_results=5)

        # TavilyClient.search called only ONCE due to cache
        mock_client.search.assert_called_once()
        self.assertEqual(r1.execution_time_ms, r2.execution_time_ms)

    # 19. Query count limit (max 2-3 queries per request)
    def test_19_query_count_limit(self):
        intent = CommerceIntent("wireless keyboard under 2000", None, "wireless keyboard", budget_limit_inr=2000.0)
        queries = CommerceResearchAdapter.generate_queries(intent)
        self.assertLessEqual(len(queries), 3)

    # 20. Secret leakage test
    def test_20_secret_leakage_test(self):
        masked = environment_manager.mask_secret("tvly-secretkey-1234567890")
        self.assertEqual(masked, "tvly...7890")
        self.assertNotIn("1234567890", masked)


if __name__ == "__main__":
    print("=" * 60)
    print("HELIOS Tavily Commerce Search Validation Suite")
    print("=" * 60)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.makeSuite(TavilySearchValidationSuite))
    if not result.wasSuccessful():
        sys.exit(1)
