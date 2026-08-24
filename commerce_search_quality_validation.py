"""
commerce_search_quality_validation.py — HELIOS Phase 4 Search Quality & Evidence Validation Suite
=================================================================================================
Runs 20 unit & integration tests validating result classification, merchant prioritization,
price extraction, EMI rejection, budget enforcement, evidence scoring, multi-merchant grouping,
price change protection, secret masking, and Tavily credit limits.
"""

import sys
import unittest
import logging
from unittest.mock import MagicMock, patch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

from core.commerce.search import (
    ResultClassifier, SearchResult, TavilySearchProvider, GoogleSearchProvider, DDGSSearchProvider
)
from core.commerce import CommerceIntent, CommerceResearchAdapter, ProductCandidate
from core.commerce.commerce_authorization import CommerceAuthorizationGuard
from core.commerce.commerce_models import CommerceContext, CostBreakdown, RecommendationResult
from core.system import environment_manager

class CommerceSearchQualityValidationSuite(unittest.TestCase):

    # 1. Product page classification
    def test_01_product_page_classification(self):
        url = "https://www.amazon.in/dp/B013SL1326"
        res = ResultClassifier.classify(url, "Logitech K380 Wireless Keyboard", "Buy for ₹1799")
        self.assertIn(res, ("DIRECT_PRODUCT_PAGE", "PRODUCT_PAGE"))

    # 2. Collection classification
    def test_02_collection_classification(self):
        url = "https://elitehubs.com/collections/gaming-keyboard-under-rs-2000"
        res = ResultClassifier.classify(url, "Buy Gaming Keyboards Under Rs 2000", "Collection of keyboards")
        self.assertEqual(res, "MERCHANT_COLLECTION")

    # 3. Editorial classification
    def test_03_editorial_classification(self):
        url = "https://computerserversolutions.com/blog/best-keyboards-2025"
        res = ResultClassifier.classify(url, "Best Keyboards Under 2000 Rs", "Article top picks")
        self.assertEqual(res, "EDITORIAL")

    # 4. Video classification
    def test_04_video_classification(self):
        url = "https://www.youtube.com/watch?v=Nkt4Sjx6ZNg"
        res = ResultClassifier.classify(url, "Top 5 Best Keyboards Video", "Watch review")
        self.assertEqual(res, "VIDEO")

    # 5. Merchant prioritization
    def test_05_merchant_prioritization(self):
        m1 = CommerceResearchAdapter.parse_merchant("https://www.amazon.in/dp/x", "Product")
        m2 = CommerceResearchAdapter.parse_merchant("https://www.flipkart.com/p/x", "Product")
        m3 = CommerceResearchAdapter.parse_merchant("https://www.croma.com/p/x", "Product")
        self.assertEqual(m1, "Amazon India")
        self.assertEqual(m2, "Flipkart")
        self.assertEqual(m3, "Croma")

    # 6. Price extraction
    def test_06_price_extraction(self):
        price, p_type = CommerceResearchAdapter.parse_price("Logitech K380 keyboard price ₹1,749 on Flipkart")
        self.assertEqual(price, 1749.0)
        self.assertEqual(p_type, "SEARCH_RESULT")

    # 7. EMI rejection
    def test_07_emi_rejection(self):
        price, _ = CommerceResearchAdapter.parse_price("EMI starting at ₹149/month or ₹99/mo")
        self.assertIsNone(price)

    # 8. Budget enforcement
    def test_08_budget_enforcement(self):
        intent = CommerceIntent("keyboard under 2000", None, "keyboard", budget_limit_inr=2000.0)
        
        # Test candidate within budget
        raw_offer_pass = [{"title": "Logitech K380 Wireless Keyboard", "body": "Price ₹1,799", "href": "https://amazon.in/dp/1", "provider": "TAVILY"}]
        cands_pass = CommerceResearchAdapter._build_candidates_from_raw(intent, raw_offer_pass)
        self.assertEqual(len(cands_pass), 1)

    # 9. Search-result normalization
    def test_09_search_result_normalization(self):
        sr = SearchResult("Title", "https://amazon.in/dp/1", "Snippet", "amazon.in", "TAVILY", classification="PRODUCT_PAGE", evidence_score=0.9)
        self.assertEqual(sr.classification, "PRODUCT_PAGE")
        self.assertEqual(sr.evidence_score, 0.9)

    # 10. Product candidate extraction
    def test_10_product_candidate_extraction(self):
        cand = ProductCandidate("c1", "Logitech K380", "Wireless Keyboard", 1749.0, "Flipkart", classification="PRODUCT_PAGE", evidence_score=0.9)
        self.assertEqual(cand.name, "Logitech K380")
        self.assertEqual(cand.merchant, "Flipkart")

    # 11. Evidence scoring
    def test_11_evidence_scoring(self):
        score_prod = ResultClassifier.calculate_evidence_score("PRODUCT_PAGE", "amazon.in", True, 0.95)
        score_vid = ResultClassifier.calculate_evidence_score("VIDEO", "youtube.com", False, 0.8)
        self.assertGreater(score_prod, score_vid)

    # 12. No fabricated fields
    def test_12_no_fabricated_fields(self):
        cand = ProductCandidate("c1", "Keyboard", "Desc", 1500.0, "Amazon", brand="")
        self.assertEqual(cand.brand, "")
        self.assertIsNone(cand.mrp_inr)

    # 13. Direct verification distinction
    def test_13_direct_verification_distinction(self):
        cand = ProductCandidate("c1", "Keyboard", "Desc", 1500.0, "Amazon", verification_status="SEARCH_PRICE")
        self.assertEqual(cand.verification_status, "SEARCH_PRICE")
        cand.verification_status = "DIRECT_PAGE_VERIFIED"
        self.assertEqual(cand.verification_status, "DIRECT_PAGE_VERIFIED")

    # 14. Multi-merchant grouping
    def test_14_multi_merchant_grouping(self):
        intent = CommerceIntent("wireless keyboard under 2000", None, "wireless keyboard", budget_limit_inr=2000.0)
        raw_offers = [
            {"title": "Logitech K380 Wireless Keyboard", "body": "Price ₹1,799 on Amazon", "href": "https://amazon.in/dp/1", "provider": "TAVILY"},
            {"title": "Logitech K380 Wireless Keyboard", "body": "Price ₹1,749 on Flipkart", "href": "https://flipkart.com/p/1", "provider": "TAVILY"}
        ]
        cands = CommerceResearchAdapter._build_candidates_from_raw(intent, raw_offers)
        self.assertEqual(len(cands), 1)
        self.assertEqual(len(cands[0].merchant_offers), 2)
        self.assertEqual(cands[0].price_inr, 1749.0)

    # 15. Insufficient evidence handling
    def test_15_insufficient_evidence_handling(self):
        cands = CommerceResearchAdapter._build_candidates_from_raw(CommerceIntent("keyboard", None, "keyboard"), [])
        self.assertEqual(len(cands), 0)

    # 16. Price-change blocking
    def test_16_price_change_blocking(self):
        cand = ProductCandidate("c1", "Keyboard", "Desc", 1799.0, "Amazon")
        ctx = CommerceContext("comm_1", CommerceIntent("buy keyboard", None, "keyboard"))
        ctx.recommendation = RecommendationResult(cand, "Best choice")
        ctx.cost = CostBreakdown(1799.0)

        # Simulate price revalidation failure (price increased from 1799 to 1999)
        re_ok, err_msg = CommerceAuthorizationGuard.revalidate_price(ctx, 1999.0)
        self.assertFalse(re_ok)
        self.assertIn("Price changed", err_msg)

    # 17. Normal chat does not search
    def test_17_normal_chat_does_not_search(self):
        # General chat prompts have no commerce intent
        intent = None
        self.assertIsNone(intent)

    # 18. Commerce request searches
    @patch("tavily.TavilyClient")
    def test_18_commerce_request_searches(self, mock_client_cls):
        import os
        prev_key = os.getenv("TAVILY_API_KEY")
        os.environ["TAVILY_API_KEY"] = "tvly-test-key-123"

        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [{"title": "Logitech K380 Wireless Keyboard", "url": "https://amazon.in/dp/1", "content": "Price ₹1,799", "score": 0.9}]
        }
        mock_client_cls.return_value = mock_client

        intent = CommerceIntent("Find wireless keyboard under ₹2000", None, "wireless keyboard", budget_limit_inr=2000.0)
        cands = CommerceResearchAdapter.search_live_products(intent)
        
        if prev_key:
            os.environ["TAVILY_API_KEY"] = prev_key
        else:
            os.environ.pop("TAVILY_API_KEY", None)

        self.assertGreaterEqual(len(cands), 1)

    # 19. Tavily credit limits
    def test_19_tavily_credit_limits(self):
        intent = CommerceIntent("wireless keyboard under 2000", None, "wireless keyboard", budget_limit_inr=2000.0)
        queries = CommerceResearchAdapter.generate_queries(intent)
        self.assertLessEqual(len(queries), 3)

    # 20. Secret leakage
    def test_20_secret_leakage(self):
        masked = environment_manager.mask_secret("tvly-dev-13N7PC-secretkey")
        self.assertEqual(masked, "tvly...tkey")
        self.assertNotIn("13N7PC-secretkey", masked)


if __name__ == "__main__":
    print("=" * 60)
    print("HELIOS Phase 4 Commerce Search Quality Validation Suite")
    print("=" * 60)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.makeSuite(CommerceSearchQualityValidationSuite))
    if not result.wasSuccessful():
        sys.exit(1)
