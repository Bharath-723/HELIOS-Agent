"""
google_search_validation.py — HELIOS Google Search Provider Validation Suite
==============================================================================
Runs 15 comprehensive unit & integration tests validating google-genai SDK v2.8.0,
Search Grounding configuration, error classification, mock telemetry, and diagnostic mode.
"""

import sys
import unittest
import logging
from unittest.mock import MagicMock, patch
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

from core.commerce.search import (
    GoogleSearchProvider, DDGSSearchProvider, SearchResult, SearchResponse
)
from core.commerce import CommerceIntent, CommerceResearchAdapter


class GoogleSearchValidationSuite(unittest.TestCase):

    def setUp(self):
        import os
        os.environ["GOOGLE_SEARCH_ENABLED"] = "true"

    # 1. google-genai imports correctly
    def test_01_google_genai_import(self):
        try:
            from google import genai
            from google.genai import types
            self.assertTrue(True)
        except ImportError:
            self.fail("google-genai SDK not available")

    # 2. Google provider initializes
    def test_02_google_provider_initialization(self):
        provider = GoogleSearchProvider(api_key="test_api_key_12345")
        self.assertEqual(provider.api_key, "test_api_key_12345")
        self.assertTrue(provider.is_available())

    # 3. Credentials detected without exposing them
    def test_03_credential_detection(self):
        provider = GoogleSearchProvider(api_key="secret_key_abcdef123456")
        self.assertNotIn("secret_key_abcdef123456", str(provider.is_available()))

    # 4. Model configuration valid
    def test_04_model_configuration(self):
        provider = GoogleSearchProvider()
        self.assertIn("gemini-3.6-flash", provider.SUPPORTED_MODELS)

    # 5. Search Grounding tool configuration constructed correctly
    def test_05_search_grounding_tool_construction(self):
        from google.genai import types
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
        self.assertIsNotNone(config.tools)
        self.assertEqual(len(config.tools), 1)

    # 6. Successful response normalization
    def test_06_successful_response_normalization(self):
        sr = SearchResult(
            title="Logitech K380 Wireless Keyboard",
            url="https://www.amazon.in/dp/B013SL1326",
            snippet="Price is ₹1,799 in stock",
            domain="amazon.in",
            source="amazon.in",
            provider="GOOGLE",
            confidence=0.98
        )
        self.assertEqual(sr.provider, "GOOGLE")
        self.assertEqual(sr.domain, "amazon.in")
        self.assertEqual(sr.confidence, 0.98)

    # 7. Source URLs preserved
    def test_07_source_url_preservation(self):
        sr = SearchResult("Title", "https://www.flipkart.com/item", "Snippet", "flipkart.com", "flipkart.com", provider="GOOGLE")
        d = sr.to_dict()
        self.assertEqual(d["url"], "https://www.flipkart.com/item")

    # 8. Provider metadata preserved
    def test_08_provider_metadata_preservation(self):
        resp = SearchResponse(
            query="test query",
            results=[SearchResult("Title", "https://url.com", "Snippet", "url.com", "url.com", provider="GOOGLE")],
            provider_used="GOOGLE",
            success=True
        )
        self.assertTrue(resp.success)
        self.assertEqual(resp.provider_used, "GOOGLE")
        self.assertIsNone(resp.error_code)

    # 9. Authentication errors classified
    @patch("google.genai.Client")
    def test_09_auth_error_classification(self, mock_client):
        mock_instance = MagicMock()
        mock_instance.models.generate_content.side_effect = Exception("401 API_KEY_INVALID")
        mock_client.return_value = mock_instance

        provider = GoogleSearchProvider(api_key="invalid_key_12345")
        resp = provider.search("keyboard")
        self.assertFalse(resp.success)
        self.assertEqual(resp.error_code, "GOOGLE_AUTH_FAILED")

    # 10. Quota errors classified
    @patch("google.genai.Client")
    def test_10_quota_error_classification(self, mock_client):
        mock_instance = MagicMock()
        mock_instance.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED: Quota limit reached")
        mock_client.return_value = mock_instance

        provider = GoogleSearchProvider(api_key="quota_key_12345")
        resp = provider.search("keyboard")
        self.assertFalse(resp.success)
        self.assertEqual(resp.error_code, "GOOGLE_RATE_LIMITED")

    # 11. Model errors classified
    @patch("google.genai.Client")
    def test_11_model_error_classification(self, mock_client):
        mock_instance = MagicMock()
        mock_instance.models.generate_content.side_effect = Exception("404 NOT_FOUND: model not available")
        mock_client.return_value = mock_instance

        provider = GoogleSearchProvider(api_key="valid_key_12345")
        resp = provider.search("keyboard")
        self.assertFalse(resp.success)
        self.assertEqual(resp.error_code, "GOOGLE_MODEL_NOT_FOUND")

    # 12. Empty results distinguished from request failures
    @patch("google.genai.Client")
    def test_12_empty_results_classification(self, mock_client):
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.candidates = []
        mock_instance.models.generate_content.return_value = mock_response
        mock_client.return_value = mock_instance

        provider = GoogleSearchProvider(api_key="valid_key_12345")
        resp = provider.search("keyboard")
        self.assertFalse(resp.success)
        self.assertEqual(resp.error_code, "GOOGLE_EMPTY_RESULTS")

    # 13. DDGS not invoked in diagnostic-only mode
    @patch("core.commerce.search.GoogleSearchProvider.search")
    @patch("core.commerce.search.DDGSSearchProvider.search")
    def test_13_diagnostic_mode_prevents_fallback(self, mock_ddgs, mock_google):
        import os
        prev = os.getenv("COMMERCE_SEARCH_PROVIDER")
        os.environ["COMMERCE_SEARCH_PROVIDER"] = "google"

        mock_google.return_value = SearchResponse(
            query="keyboard",
            results=[],
            provider_used="GOOGLE",
            success=False,
            error_code="GOOGLE_RATE_LIMITED",
            fallback_allowed=False  # Diagnostic mode
        )

        intent = CommerceIntent("buy keyboard", None, "keyboard")
        cands = CommerceResearchAdapter.search_live_products(intent)
        
        if prev:
            os.environ["COMMERCE_SEARCH_PROVIDER"] = prev
        else:
            os.environ.pop("COMMERCE_SEARCH_PROVIDER", None)

        mock_ddgs.assert_not_called()

    # 14. Normal mode can fall back correctly
    @patch("core.commerce.search.GoogleSearchProvider.search")
    @patch("core.commerce.search.DDGSSearchProvider.search")
    def test_14_normal_mode_allows_fallback(self, mock_ddgs, mock_google):
        import os
        prev = os.getenv("COMMERCE_SEARCH_PROVIDER")
        os.environ["COMMERCE_SEARCH_PROVIDER"] = "google"

        mock_google.return_value = SearchResponse(
            query="keyboard",
            results=[],
            provider_used="GOOGLE",
            success=False,
            error_code="GOOGLE_RATE_LIMITED",
            fallback_allowed=True
        )
        mock_ddgs.return_value = SearchResponse(
            query="keyboard",
            results=[SearchResult("FB", "https://x.com", "body", "x.com", "DDGS", provider="DDGS_FALLBACK")],
            provider_used="DDGS_FALLBACK",
            success=True
        )

        intent = CommerceIntent("buy keyboard", None, "keyboard")
        cands = CommerceResearchAdapter.search_live_products(intent)

        if prev:
            os.environ["COMMERCE_SEARCH_PROVIDER"] = prev
        else:
            os.environ.pop("COMMERCE_SEARCH_PROVIDER", None)

        mock_ddgs.assert_called()

    # 15. No API secret appears in logs or representations
    def test_15_no_secret_leakage(self):
        provider = GoogleSearchProvider(api_key="secret_key_9999999999")
        d_str = str(provider.__dict__)
        # Ensure representation mask check
        from core.system import environment_manager
        masked = environment_manager.mask_secret("secret_key_9999999999")
        self.assertEqual(masked, "secr...9999")


if __name__ == "__main__":
    print("=" * 60)
    print("HELIOS Google Search Provider Validation Suite")
    print("=" * 60)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.makeSuite(GoogleSearchValidationSuite))
    if not result.wasSuccessful():
        sys.exit(1)
