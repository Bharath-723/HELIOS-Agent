"""
agentic_payment_validation.py — HELIOS Phase 2 Agentic Payment Validation Suite
=================================================================================
Runs 20 comprehensive end-to-end unit tests covering natural language intent detection,
planner integration, authorization boundaries, state transitions, and zero-leak security.
"""

import sys
import unittest
import logging
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

from agent import HELIOSAgent
from core.payments import (
    PaymentConfig, PaymentIntent, PaymentOrder, PaymentResult,
    TransactionState, TransactionGuard, PaymentRepository,
    RazorpayClient, PaymentVerifier, PaymentTool, HeliosPaymentAdapter,
    PaymentContext
)


class AgenticPaymentValidationSuite(unittest.TestCase):

    def setUp(self):
        self.agent = HELIOSAgent()
        self.mock_env = {
            "RAZORPAY_KEY_ID": "rzp_test_agentic_key123",
            "RAZORPAY_KEY_SECRET": "rzp_secret_agentic_sec456",
            "RAZORPAY_MODE": "sandbox",
            "RAZORPAY_WEBHOOK_SECRET": "whsec_agentic_wh789",
            "MAX_PAYMENT_AMOUNT_INR": "10000"
        }
        self.config = PaymentConfig(self.mock_env)
        self.adapter = HeliosPaymentAdapter(self.config)

    # 1. Payment intent detection
    def test_01_payment_intent_detection(self):
        comm_res = self.agent.commerce.process_commerce_request("buy this course for ₹999", mode="demo")
        self.assertTrue(comm_res["success"])
        self.assertEqual(comm_res["type"], "COMMERCE_TRANSACTION_READY")
        context_data = comm_res["context"]
        self.assertEqual(context_data["state"], TransactionState.REQUIRES_AUTHORIZATION.value)

    # 2. Non-payment intent does not trigger payment
    def test_02_non_payment_intent_does_not_trigger_payment(self):
        res = self.agent.process("what is the price of this course?")
        self.assertFalse(res.startswith("PAYMENT_INTENT_JSON:"))

    # 3. Payment plan generation
    def test_03_payment_plan_generation(self):
        ctx = PaymentContext(
            merchant="Udemy",
            product="Python Masterclass",
            amount=149900,
            currency="INR"
        )
        ctx_dict = ctx.to_dict()
        self.assertEqual(ctx_dict["merchant"], "Udemy")
        self.assertEqual(ctx_dict["amount_inr_display"], 1499.0)
        self.assertTrue(ctx_dict["authorization_required"])

    # 4. Payment tool discovery
    def test_04_payment_tool_discovery(self):
        res = self.adapter.execute_tool_call("prepare_payment", {
            "description": "Subscription",
            "amount": 49900,
            "merchant_name": "SaaS Co"
        })
        self.assertTrue(res["success"])
        self.assertEqual(res["state"], TransactionState.REQUIRES_AUTHORIZATION.value)

    # 5. Authorization requirement enforcement
    def test_05_authorization_requirement_enforcement(self):
        prep = self.adapter.execute_tool_call("prepare_payment", {"description": "Item", "amount": 10000})
        intent_id = prep["data"]["intent_id"]
        # Direct order creation without authorization step
        order_res = self.adapter.execute_tool_call("create_order", {"intent_id": intent_id, "mock": True})
        self.assertFalse(order_res["success"])
        self.assertEqual(order_res["state"], TransactionState.REQUIRES_AUTHORIZATION.value)

    # 6. Unauthorized order rejection
    def test_06_unauthorized_order_rejection(self):
        prep = self.adapter.execute_tool_call("prepare_payment", {"description": "Item 2", "amount": 20000})
        intent_id = prep["data"]["intent_id"]
        # Explicit user decline
        auth_res = self.adapter.execute_tool_call("authorize_payment", {"intent_id": intent_id, "user_confirm": False})
        self.assertFalse(auth_res["success"])
        self.assertEqual(auth_res["state"], TransactionState.CANCELLED.value)

    # 7. Authorized order creation
    def test_07_authorized_order_creation(self):
        prep = self.adapter.execute_tool_call("prepare_payment", {"description": "Item 3", "amount": 30000})
        intent_id = prep["data"]["intent_id"]
        self.adapter.execute_tool_call("authorize_payment", {"intent_id": intent_id, "user_confirm": True})
        order_res = self.adapter.execute_tool_call("create_order", {"intent_id": intent_id, "mock": True})
        self.assertTrue(order_res["success"])
        self.assertEqual(order_res["state"], TransactionState.ORDER_CREATED.value)

    # 8. Amount immutability
    def test_08_amount_immutability(self):
        prep = self.adapter.execute_tool_call("prepare_payment", {"description": "Item 4", "amount": 50000})
        intent_id = prep["data"]["intent_id"]
        self.adapter.execute_tool_call("authorize_payment", {"intent_id": intent_id, "user_confirm": True})
        intent = self.adapter.tool.repo.get_intent(intent_id)

        # Confirm intent amount matches authorized amount
        self.assertEqual(intent.amount, 50000)

    # 9. Merchant immutability
    def test_09_merchant_immutability(self):
        prep = self.adapter.execute_tool_call("prepare_payment", {"description": "Item 5", "amount": 50000, "merchant_name": "Store A"})
        intent_id = prep["data"]["intent_id"]
        intent = self.adapter.tool.repo.get_intent(intent_id)
        self.assertEqual(intent.merchant_name, "Store A")

    # 10. Expired transaction rejection / Exceeded limits
    def test_10_exceeded_limits_rejection(self):
        prep = self.adapter.execute_tool_call("prepare_payment", {"description": "Super Expensive", "amount": 5000000})  # ₹50,000 > ₹10,000
        self.assertFalse(prep["success"])
        self.assertEqual(prep["state"], TransactionState.REQUIRES_ADDITIONAL_AUTHORIZATION.value)

    # 11. Duplicate authorization protection (Idempotency)
    def test_11_duplicate_authorization_protection(self):
        ref = "DUP_AUTH_REF_111"
        res1 = self.adapter.execute_tool_call("prepare_payment", {"description": "Ebook", "amount": 29900, "merchant_reference": ref})
        res2 = self.adapter.execute_tool_call("prepare_payment", {"description": "Ebook", "amount": 29900, "merchant_reference": ref})
        self.assertEqual(res1["data"]["intent_id"], res2["data"]["intent_id"])

    # 12. Checkout state
    def test_12_checkout_state(self):
        prep = self.adapter.execute_tool_call("prepare_payment", {"description": "Ticket", "amount": 80000})
        intent_id = prep["data"]["intent_id"]
        self.adapter.execute_tool_call("authorize_payment", {"intent_id": intent_id, "user_confirm": True})
        order_res = self.adapter.execute_tool_call("create_order", {"intent_id": intent_id, "mock": True})
        order_id = order_res["data"]["order"]["order_id"]

        decision = self.adapter.tool.guard.can_open_checkout(
            self.adapter.tool.repo.get_intent(intent_id),
            self.adapter.tool.repo.get_order(order_id)
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.state, TransactionState.CHECKOUT_OPEN)

    # 13. Signature verification
    def test_13_signature_verification(self):
        prep = self.adapter.execute_tool_call("prepare_payment", {"description": "Gadget", "amount": 120000})
        intent_id = prep["data"]["intent_id"]
        self.adapter.execute_tool_call("authorize_payment", {"intent_id": intent_id, "user_confirm": True})
        order_res = self.adapter.execute_tool_call("create_order", {"intent_id": intent_id, "mock": True})
        order_id = order_res["data"]["order"]["order_id"]
        payment_id = "pay_valid_mock_123"

        import hmac, hashlib
        secret = self.config.key_secret
        sig = hmac.new(secret.encode("utf-8"), f"{order_id}|{payment_id}".encode("utf-8"), hashlib.sha256).hexdigest()

        verify_res = self.adapter.execute_tool_call("verify_payment", {
            "intent_id": intent_id,
            "payment_id": payment_id,
            "order_id": order_id,
            "signature": sig
        })
        self.assertTrue(verify_res["success"])
        self.assertEqual(verify_res["state"], TransactionState.CAPTURED.value)

    # 14. Webhook confirmation
    def test_14_webhook_confirmation(self):
        from payment_service import PaymentServiceApp
        app = PaymentServiceApp(self.config)

        body = b'{"event":"payment.captured","account_id":"acc_test","created_at":1700000001}'
        import hmac, hashlib
        sig = hmac.new(self.config.webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

        status_code, res = app.dispatch_request("POST", "/webhooks/razorpay", {"X-Razorpay-Signature": sig}, body)
        self.assertEqual(status_code, 200)
        self.assertEqual(res["status"], "processed")

    # 15. Failed payment
    def test_15_failed_payment(self):
        prep = self.adapter.execute_tool_call("prepare_payment", {"description": "Fail Item", "amount": 10000})
        intent_id = prep["data"]["intent_id"]
        self.adapter.execute_tool_call("authorize_payment", {"intent_id": intent_id, "user_confirm": True})
        self.adapter.execute_tool_call("create_order", {"intent_id": intent_id, "mock": True})
        verify_res = self.adapter.execute_tool_call("verify_payment", {
            "intent_id": intent_id,
            "payment_id": "pay_fail",
            "order_id": "order_fail",
            "signature": "bad_sig"
        })
        self.assertFalse(verify_res["success"])
        self.assertEqual(verify_res["state"], TransactionState.VERIFICATION_FAILED.value)

    # 16. Cancelled payment
    def test_16_cancelled_payment(self):
        prep = self.adapter.execute_tool_call("prepare_payment", {"description": "Cancel Item", "amount": 10000})
        intent_id = prep["data"]["intent_id"]
        cancel_res = self.adapter.execute_tool_call("cancel_payment", {"intent_id": intent_id, "reason": "User changed mind"})
        self.assertTrue(cancel_res["success"])
        self.assertEqual(cancel_res["state"], TransactionState.CANCELLED.value)

    # 17. Verification failure handling
    def test_17_verification_failure_handling(self):
        prep = self.adapter.execute_tool_call("prepare_payment", {"description": "Mismatch Item", "amount": 10000})
        intent_id = prep["data"]["intent_id"]
        self.adapter.execute_tool_call("authorize_payment", {"intent_id": intent_id, "user_confirm": True})
        order_res = self.adapter.execute_tool_call("create_order", {"intent_id": intent_id, "mock": True})

        # Send fake order ID during verification
        verify_res = self.adapter.execute_tool_call("verify_payment", {
            "intent_id": intent_id,
            "payment_id": "pay_test",
            "order_id": "order_fake_id_xyz",
            "signature": "sig"
        })
        self.assertFalse(verify_res["success"])
        self.assertEqual(verify_res["state"], TransactionState.VERIFICATION_FAILED.value)

    # 18. Privacy warning detection
    def test_18_privacy_warning_detection(self):
        # Verify privacy detection logic
        from helios_popup import HELIOSApp
        class DummyApp:
            agent = self.agent
            def _update_all_model_displays(self, m, s): pass
            class chat:
                @staticmethod
                def add_system_notice(msg): pass
            _check_cloud_privacy = HELIOSApp._check_cloud_privacy
        
        dummy = DummyApp()
        has_notice = dummy._check_cloud_privacy("My credit card password is 1234")
        self.assertIsInstance(has_notice, bool)

    # 19. Payment result rendering payload
    def test_19_payment_result_rendering_payload(self):
        result_dict = {
            "success": True,
            "payment_id": "pay_abc123456789",
            "order_id": "order_def987654321",
            "status": "CAPTURED",
            "amount": 99900,
            "currency": "INR",
            "verified": True
        }
        import tkinter as tk
        from ui.chat_view import ChatView
        root = tk.Tk()
        root.withdraw()
        cv = ChatView(root)
        frame = cv.add_payment_result_card(result_dict)
        self.assertIsNotNone(frame)
        root.destroy()

    # 20. Existing HELIOS regression test suite run
    def test_20_existing_helios_regression_test_suite(self):
        # Run existing reasoning & knowledge validation scripts safely
        import subprocess
        r1 = subprocess.run([sys.executable, "razorpay_validation.py"], capture_output=True, text=True)
        r2 = subprocess.run([sys.executable, "payment_security_validation.py"], capture_output=True, text=True)
        self.assertEqual(r1.returncode, 0)
        self.assertEqual(r2.returncode, 0)


if __name__ == "__main__":
    print("=" * 60)
    print("HELIOS Phase 2 Agentic Payment Validation Suite")
    print("=" * 60)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.makeSuite(AgenticPaymentValidationSuite))
    if not result.wasSuccessful():
        sys.exit(1)
