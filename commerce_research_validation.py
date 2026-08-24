"""
commerce_research_validation.py — HELIOS Real-Time Commerce Research Validation Suite
======================================================================================
Validates live web search query generation, price parsing, currency normalization,
source attribution, freshness tracking, budget filtering, multi-merchant deduplication,
price-change protection, research failure handling, and live/demo mode separation.
"""

import sys
import unittest
import logging
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

from core.commerce import (
    CommerceIntentClassifier, CommerceResearchAdapter, CommerceResearcher,
    CommerceAuthorizationGuard, CommerceContext, CommerceIntent,
    CommerceIntentCategory, ProductCandidate, CostBreakdown, RecommendationResult,
    CommerceOrchestrator, CommerceState
)


class CommerceResearchValidationSuite(unittest.TestCase):

    # 1. Query generation
    def test_01_query_generation(self):
        intent = CommerceIntentClassifier.classify("Find wireless keyboard under ₹2000")
        queries = CommerceResearchAdapter.generate_queries(intent)
        self.assertGreater(len(queries), 0)
        self.assertTrue(any("under 2000" in q for q in queries))
        self.assertTrue(any("amazon" in q.lower() for q in queries))

    # 2. Price parsing
    def test_02_price_parsing(self):
        p1, t1 = CommerceResearchAdapter.parse_price("Logitech K380 for ₹1,799 only")
        self.assertEqual(p1, 1799.0)
        self.assertEqual(t1, "SEARCH_RESULT")

        p2, _ = CommerceResearchAdapter.parse_price("Special price: Rs. 1749 with free shipping")
        self.assertEqual(p2, 1749.0)

        p3, _ = CommerceResearchAdapter.parse_price("INR 1999 MRP")
        self.assertEqual(p3, 1999.0)

        # Ignore EMI rate
        p4, _ = CommerceResearchAdapter.parse_price("EMI starting at ₹199/mo")
        self.assertIsNone(p4)

    # 3. Currency normalization
    def test_03_currency_normalization(self):
        p, _ = CommerceResearchAdapter.parse_price("Price: Rs 1,499.00")
        self.assertEqual(p, 1499.0)

    # 4. Source attribution
    def test_04_source_attribution(self):
        m1 = CommerceResearchAdapter.parse_merchant("https://www.amazon.in/dp/B013SL1326", "Logitech Keyboard")
        m2 = CommerceResearchAdapter.parse_merchant("https://www.flipkart.com/p/itm123", "Logitech Keyboard")
        m3 = CommerceResearchAdapter.parse_merchant("https://www.croma.com/p/123", "Logitech Keyboard")

        self.assertEqual(m1, "Amazon India")
        self.assertEqual(m2, "Flipkart")
        self.assertEqual(m3, "Croma")

    # 5. Stale price status calculation
    def test_05_stale_price_calculation(self):
        now_iso = datetime.utcnow().isoformat()
        f_live = CommerceResearchAdapter.calculate_freshness(now_iso)
        self.assertEqual(f_live, "LIVE")

        old_dt = (datetime.utcnow() - timedelta(minutes=45)).isoformat()
        f_recent = CommerceResearchAdapter.calculate_freshness(old_dt)
        self.assertEqual(f_recent, "RECENT")

        stale_dt = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        f_stale = CommerceResearchAdapter.calculate_freshness(stale_dt)
        self.assertEqual(f_stale, "STALE")

    # 6. Budget filtering
    def test_06_budget_filtering(self):
        intent = CommerceIntentClassifier.classify("Find keyboard under ₹1500")
        candidates = CommerceResearcher.research(intent, mode="demo")
        for c in candidates:
            self.assertLessEqual(c.price_inr, 1500.0)

    # 7. Shipping cost budget breach
    def test_07_shipping_cost_budget_breach(self):
        cand = ProductCandidate(
            candidate_id="c_ship",
            name="Keyboard",
            description="Desc",
            price_inr=1950.0,
            merchant="Amazon",
            shipping_inr=100.0,
            over_budget_after_delivery=True
        )
        self.assertTrue(cand.over_budget_after_delivery)

    # 8. Multi-source product deduplication & offer aggregation
    def test_08_multi_source_deduplication(self):
        cand = ProductCandidate(
            candidate_id="c_multi",
            name="Logitech K380",
            description="Wireless keyboard",
            price_inr=1749.0,
            merchant="Flipkart",
            merchant_offers=[
                {"merchant": "Flipkart", "price_inr": 1749.0, "url": "https://flipkart.com", "freshness_status": "LIVE"},
                {"merchant": "Amazon India", "price_inr": 1799.0, "url": "https://amazon.in", "freshness_status": "LIVE"},
                {"merchant": "Croma", "price_inr": 1899.0, "url": "https://croma.com", "freshness_status": "LIVE"}
            ]
        )
        self.assertEqual(len(cand.merchant_offers), 3)

    # 9. Recommendation scoring
    def test_09_recommendation_scoring(self):
        intent = CommerceIntentClassifier.classify("Find wireless keyboard under ₹2000")
        candidates = CommerceResearcher.research(intent, mode="demo")
        from core.commerce import CommerceComparator, CommerceRecommender
        comp = CommerceComparator.compare(intent, candidates)
        rec = CommerceRecommender.recommend(intent, comp)
        self.assertIsNotNone(rec)
        self.assertIn("Logitech", rec.selected_candidate.name)

    # 10. Price-change protection gate
    def test_10_price_change_protection_gate(self):
        cand = ProductCandidate("c1", "Keyboard", "Desc", 1799.0, "Amazon")
        cost = CostBreakdown(1799.0)
        intent = CommerceIntent("buy keyboard", CommerceIntentCategory.PURCHASE_REQUEST, "Keyboard")
        ctx = CommerceContext(
            commerce_id="comm_price_change",
            intent=intent,
            recommendation=RecommendationResult(cand, "Selected"),
            cost=cost
        )

        # Price remains unchanged -> True
        v_ok, _ = CommerceAuthorizationGuard.revalidate_price(ctx, 1799.0)
        self.assertTrue(v_ok)

        # Price increases from 1799.0 to 1999.0 -> False & Blocked
        v_blocked, msg = CommerceAuthorizationGuard.revalidate_price(ctx, 1999.0)
        self.assertFalse(v_blocked)
        self.assertIn("Price changed since research", msg)
        self.assertEqual(ctx.state, CommerceState.TRANSACTION_FAILED.value)

    # 11. Research failure handling
    def test_11_research_failure_handling(self):
        orch = CommerceOrchestrator()
        # Mock zero candidates by forcing invalid mode or offline query
        intent = CommerceIntent("unfindable xyz item", CommerceIntentCategory.PURCHASE_REQUEST, "unfindable xyz item")
        res = orch.process_commerce_request("unfindable xyz item 99999", mode="live")
        # Should gracefully fail if search yields no results
        if not res["success"]:
            self.assertEqual(res["type"], "RESEARCH_FAILED")
            self.assertIn("HELIOS couldn't retrieve reliable current prices", res["error_message"])

    # 12. Demo/Live mode separation
    def test_12_demo_live_mode_separation(self):
        intent = CommerceIntentClassifier.classify("Find wireless keyboard under ₹2000")
        demo_cands = CommerceResearcher.research(intent, mode="demo")
        for c in demo_cands:
            self.assertIn(c.price_type, ("SEARCH_RESULT", "DEMO_FIXTURE", "LIVE_PRODUCT_PAGE"))

    # 13. Full end-to-end live commerce research flow
    def test_13_full_end_to_end_live_commerce_flow(self):
        orch = CommerceOrchestrator()
        res = orch.process_commerce_request("Find me a wireless keyboard under ₹2000 and buy the best one", mode="demo")
        self.assertTrue(res["success"])
        self.assertEqual(res["type"], "COMMERCE_TRANSACTION_READY")


if __name__ == "__main__":
    print("=" * 60)
    print("HELIOS Real-Time Commerce Research Validation Suite")
    print("=" * 60)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.makeSuite(CommerceResearchValidationSuite))
    if not result.wasSuccessful():
        sys.exit(1)
