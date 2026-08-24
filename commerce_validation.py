"""
commerce_validation.py — HELIOS Phase 3 End-to-End Commerce Validation Suite
=============================================================================
Runs 20 comprehensive unit and integration tests covering intent classification,
product research, comparison matrix generation, explainable recommendations, cost calculations,
Razorpay subsystem bridge, authorization boundaries, signature verifications, and memory recording.
"""

import sys
import unittest
import logging
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

from agent import HELIOSAgent
from core.payments import PaymentConfig, TransactionState
from core.commerce import (
    CommerceOrchestrator, CommerceIntentClassifier, CommerceResearcher,
    CommerceComparator, CommerceRecommender, CommerceCalculator,
    CommerceTransactionBridge, CommerceAuthorizationGuard, CommerceVerifier,
    CommerceMemoryRecorder, CommerceDemoEngine, CommerceIntentCategory, CommerceState,
    ProductCandidate, CostBreakdown, RecommendationResult, CommerceContext, CommerceIntent
)


class CommerceValidationSuite(unittest.TestCase):

    def setUp(self):
        self.agent = HELIOSAgent()
        self.orchestrator = self.agent.commerce

    # 1. Information-only request
    def test_01_information_only_request(self):
        res = self.agent.process("What is the best keyboard under ₹2000?")
        self.assertFalse(res.startswith("COMMERCE_INTENT_JSON:"))
        self.assertTrue("Recommended" in res or "Keyboard" in res)

    # 2. Research request
    def test_02_research_request(self):
        intent = CommerceIntentClassifier.classify("Research options for a wireless keyboard under ₹2000")
        candidates = CommerceResearcher.research(intent, mode="demo")
        self.assertGreater(len(candidates), 0)
        self.assertTrue(any(c.price_inr <= 2000 for c in candidates))

    # 3. Purchase preparation
    def test_03_purchase_preparation(self):
        intent = CommerceIntentClassifier.classify("Find the best keyboard under ₹2000 and prepare the purchase")
        self.assertEqual(intent.category, CommerceIntentCategory.PURCHASE_PREPARATION)

    # 4. Purchase request
    def test_04_purchase_request(self):
        comm_res = self.orchestrator.process_commerce_request("Find me a keyboard under ₹2000 and buy the best one", mode="demo")
        self.assertTrue(comm_res["success"])
        self.assertEqual(comm_res["type"], "COMMERCE_TRANSACTION_READY")

    # 5. Payment-only request
    def test_05_payment_only_request(self):
        intent = CommerceIntentClassifier.classify("Pay ₹500")
        self.assertEqual(intent.category, CommerceIntentCategory.PAYMENT_ONLY)
        self.assertEqual(intent.budget_limit_inr, 500.0)

    # 6. Budget constraint
    def test_06_budget_constraint(self):
        intent = CommerceIntentClassifier.classify("Find a gift under ₹500")
        candidates = CommerceResearcher.research(intent, mode="demo")
        for c in candidates:
            self.assertLessEqual(c.price_inr, 500.0)

    # 7. Recommendation selection
    def test_07_recommendation_selection(self):
        intent = CommerceIntentClassifier.classify("Find wireless keyboard under ₹2000")
        candidates = CommerceResearcher.research(intent, mode="demo")
        comparison = CommerceComparator.compare(intent, candidates)
        recommendation = CommerceRecommender.recommend(intent, comparison)
        self.assertIsNotNone(recommendation)
        self.assertIn("budget", recommendation.reason.lower())

    # 8. Cost calculation
    def test_08_cost_calculation(self):
        cand = ProductCandidate("test_c", "Item", "Desc", 1799.0, "Store")
        cost = CommerceCalculator.calculate(cand)
        self.assertEqual(cost.total_inr, 1799.0)
        self.assertEqual(cost.total_paise, 179900)
        self.assertTrue(cost.is_exact_total)

    # 9. Authorization required
    def test_09_authorization_required(self):
        res = self.orchestrator.process_commerce_request("Buy a keyboard for ₹1799", mode="demo")
        context_data = res["context"]
        self.assertEqual(context_data["state"], CommerceState.REQUIRES_AUTHORIZATION.value)

    # 10. Authorization denied
    def test_10_authorization_denied(self):
        bridge = CommerceTransactionBridge()
        prep = bridge.adapter.execute_tool_call("prepare_payment", {"description": "Item", "amount": 10000})
        intent_id = prep["data"]["intent_id"]
        auth_res = bridge.authorize_transaction(intent_id, user_confirm=False)
        self.assertFalse(auth_res["success"])
        self.assertEqual(auth_res["state"], TransactionState.CANCELLED.value)

    # 11. Amount tampering protection
    def test_11_amount_tampering_protection(self):
        valid = CommerceAuthorizationGuard.verify_amount_immutability(179900, 179900)
        invalid = CommerceAuthorizationGuard.verify_amount_immutability(179900, 99900)
        self.assertTrue(valid)
        self.assertFalse(invalid)

    # 12. Currency tampering protection
    def test_12_currency_tampering_protection(self):
        cand = ProductCandidate("test_c", "Item", "Desc", 1000.0, "Store")
        cost = CommerceCalculator.calculate(cand)
        self.assertEqual(cost.currency, "INR")

    # 13. Payment threshold enforcement
    def test_13_payment_threshold_enforcement(self):
        cand = ProductCandidate("expensive", "Luxury Item", "Desc", 15000.0, "Luxury Store")
        cost = CostBreakdown(15000.0)
        intent = CommerceIntent("buy luxury item", CommerceIntentCategory.PURCHASE_REQUEST, "Luxury Item")
        ctx = CommerceContext(
            commerce_id="comm_exp",
            intent=intent,
            recommendation=RecommendationResult(cand, "Selected"),
            cost=cost
        )
        valid, msg = CommerceAuthorizationGuard.validate_authorization_request(ctx)
        self.assertFalse(valid)
        self.assertIn("exceeds safety threshold", msg)

    # 14. Razorpay order creation
    def test_14_razorpay_order_creation(self):
        bridge = CommerceTransactionBridge()
        prep = bridge.adapter.execute_tool_call("prepare_payment", {"description": "Item", "amount": 20000})
        intent_id = prep["data"]["intent_id"]
        bridge.authorize_transaction(intent_id, user_confirm=True)
        order_res = bridge.create_order(intent_id, mock=True)
        self.assertTrue(order_res["success"])
        self.assertEqual(order_res["state"], TransactionState.ORDER_CREATED.value)

    # 15. Payment verification
    def test_15_payment_verification(self):
        bridge = CommerceTransactionBridge()
        prep = bridge.adapter.execute_tool_call("prepare_payment", {"description": "Item", "amount": 30000})
        intent_id = prep["data"]["intent_id"]
        bridge.authorize_transaction(intent_id, user_confirm=True)
        order_res = bridge.create_order(intent_id, mock=True)
        order_id = order_res["data"]["order"]["order_id"]
        payment_id = "pay_valid_mock_999"

        import hmac, hashlib
        secret = bridge.adapter.tool.config.key_secret
        sig = hmac.new(secret.encode("utf-8"), f"{order_id}|{payment_id}".encode("utf-8"), hashlib.sha256).hexdigest()

        verify_res = bridge.verify_payment(intent_id, payment_id, order_id, sig)
        self.assertTrue(verify_res["success"])
        self.assertEqual(verify_res["state"], TransactionState.CAPTURED.value)

    # 16. Invalid signature rejection
    def test_16_invalid_signature_rejection(self):
        bridge = CommerceTransactionBridge()
        prep = bridge.adapter.execute_tool_call("prepare_payment", {"description": "Item", "amount": 30000})
        intent_id = prep["data"]["intent_id"]
        bridge.authorize_transaction(intent_id, user_confirm=True)
        order_res = bridge.create_order(intent_id, mock=True)

        verify_res = bridge.verify_payment(intent_id, "pay_fail", order_res["data"]["order"]["order_id"], "invalid_sig")
        self.assertFalse(verify_res["success"])
        self.assertEqual(verify_res["state"], TransactionState.VERIFICATION_FAILED.value)

    # 17. Duplicate payment prevention
    def test_17_duplicate_payment_prevention(self):
        ref = "REF_COMM_DUP_777"
        bridge = CommerceTransactionBridge()
        r1 = bridge.adapter.execute_tool_call("prepare_payment", {"description": "Item", "amount": 10000, "merchant_reference": ref})
        r2 = bridge.adapter.execute_tool_call("prepare_payment", {"description": "Item", "amount": 10000, "merchant_reference": ref})
        self.assertEqual(r1["data"]["intent_id"], r2["data"]["intent_id"])

    # 18. Webhook replay prevention
    def test_18_webhook_replay_prevention(self):
        from payment_service import PaymentServiceApp
        config = PaymentConfig({"RAZORPAY_KEY_ID": "k", "RAZORPAY_KEY_SECRET": "s", "RAZORPAY_WEBHOOK_SECRET": "whs"})
        app = PaymentServiceApp(config)
        body = b'{"event":"payment.captured","account_id":"acc_replay","created_at":1800000000}'
        import hmac, hashlib
        sig = hmac.new(b"whs", body, hashlib.sha256).hexdigest()

        # First call
        s1, res1 = app.dispatch_request("POST", "/webhooks/razorpay", {"X-Razorpay-Signature": sig}, body)
        self.assertEqual(s1, 200)

        # Duplicate call
        s2, res2 = app.dispatch_request("POST", "/webhooks/razorpay", {"X-Razorpay-Signature": sig}, body)
        self.assertEqual(s2, 200)
        self.assertEqual(res2["status"], "ignored")

    # 19. Memory update
    def test_19_memory_update(self):
        cand = ProductCandidate("c_mem", "Keyboard", "Desc", 1799.0, "Amazon")
        ctx = CommerceContext(
            commerce_id="comm_mem",
            intent=CommerceIntent("buy keyboard", CommerceIntentCategory.PURCHASE_REQUEST, "Keyboard"),
            recommendation=RecommendationResult(cand, "Best Choice"),
            cost=CostBreakdown(1799.0)
        )
        mem_res = CommerceMemoryRecorder.record_transaction(ctx)
        self.assertTrue(mem_res["success"])
        self.assertIn("User purchased Keyboard", mem_res["memory_summary"])

    # 20. Full end-to-end commerce flow & Demo Mode
    def test_20_full_end_to_end_commerce_flow(self):
        d1 = CommerceDemoEngine.run_demo_scenario("Find me a good wireless keyboard under ₹2,000 and buy the best one.")
        self.assertFalse(d1["stop_before_transaction"])
        self.assertTrue(d1["transaction_prepared"])

        d3 = CommerceDemoEngine.run_demo_scenario("Find me something useful under ₹1,000 but don't buy anything.")
        self.assertTrue(d3["stop_before_transaction"])
        self.assertNotIn("transaction_prepared", d3)


if __name__ == "__main__":
    print("=" * 60)
    print("HELIOS Phase 3 End-to-End Agentic Commerce Validation Suite")
    print("=" * 60)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.makeSuite(CommerceValidationSuite))
    if not result.wasSuccessful():
        sys.exit(1)
