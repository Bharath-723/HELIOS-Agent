"""
razorpay_validation.py — HELIOS Razorpay Payment Foundation Validation Suite
=============================================================================
Runs 20 comprehensive unit tests covering the isolated payment package and backend service.
Runs WITHOUT requiring live payment credentials (uses mocked responses and sandbox validation).
"""

import os
import sys
import unittest
import logging
import io

# Ensure UTF-8 output formatting
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Suppress debug logs during validation run
logging.basicConfig(level=logging.WARNING)

from core.payments import (
    PaymentConfig,
    PaymentIntent,
    PaymentOrder,
    PaymentResult,
    TransactionState,
    TransactionGuard,
    PaymentRepository,
    RazorpayClient,
    PaymentVerifier,
    PaymentTool,
    PaymentTraceTracker,
    HeliosPaymentAdapter,
    PaymentSecurityException,
    PaymentVerificationException,
)
from payment_service import PaymentServiceApp


class RazorpayValidationSuite(unittest.TestCase):

    def setUp(self):
        self.repo = PaymentRepository()
        self.mock_env = {
            "RAZORPAY_KEY_ID": "rzp_test_mock123456",
            "RAZORPAY_KEY_SECRET": "mock_secret_abcdef123456",
            "RAZORPAY_MODE": "sandbox",
            "RAZORPAY_WEBHOOK_SECRET": "mock_webhook_secret_987654",
            "MAX_PAYMENT_AMOUNT_INR": "10000"
        }
        self.config = PaymentConfig(self.mock_env)
        self.tool = PaymentTool(self.config, self.repo)
        self.app = PaymentServiceApp(self.config)

    # 1. Missing credentials
    def test_01_missing_credentials(self):
        empty_config = PaymentConfig({"RAZORPAY_KEY_ID": "", "RAZORPAY_KEY_SECRET": ""})
        self.assertFalse(empty_config.is_valid())
        self.assertIn("Payment capability unavailable", empty_config.get_status_message())

    # 2. Invalid configuration
    def test_02_invalid_configuration(self):
        invalid_mode_env = dict(self.mock_env)
        invalid_mode_env["RAZORPAY_MODE"] = "invalid_mode_xyz"
        cfg = PaymentConfig(invalid_mode_env)
        self.assertEqual(cfg.mode, "sandbox")  # Defaulted safely

    # 3. Sandbox configuration
    def test_03_sandbox_configuration(self):
        self.assertTrue(self.config.is_sandbox)
        self.assertEqual(self.config.mode, "sandbox")

    # 4. Payment intent creation
    def test_04_payment_intent_creation(self):
        res = self.tool.prepare_payment(
            description="Test Product",
            amount=99900,  # ₹999.00
            merchant_name="Acme Store",
            merchant_reference="REF_1001"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["state"], TransactionState.REQUIRES_AUTHORIZATION.value)
        self.assertIsNotNone(res["data"]["intent_id"])

    # 5. Invalid amount
    def test_05_invalid_amount(self):
        res = self.tool.prepare_payment(
            description="Invalid Item",
            amount=0,
            merchant_name="Store"
        )
        self.assertFalse(res["success"])
        self.assertEqual(res["state"], TransactionState.FAILED.value)

    # 6. Invalid currency / amount limits
    def test_06_invalid_currency_or_exceeded_amount(self):
        res = self.tool.prepare_payment(
            description="Expensive Watch",
            amount=5000000,  # ₹50,000 > ₹10,000 limit
            merchant_name="Luxury Store"
        )
        self.assertFalse(res["success"])
        self.assertEqual(res["state"], TransactionState.REQUIRES_ADDITIONAL_AUTHORIZATION.value)

    # 7. Authorization required
    def test_07_authorization_required(self):
        res_prep = self.tool.prepare_payment("Software License", 199900, "INR", "TechCorp")
        intent_id = res_prep["data"]["intent_id"]
        res_order = self.tool.create_authorized_order(intent_id, mock=True)
        self.assertFalse(res_order["success"])
        self.assertEqual(res_order["state"], TransactionState.REQUIRES_AUTHORIZATION.value)

    # 8. Unauthorized payment rejection
    def test_08_unauthorized_payment_rejection(self):
        res_prep = self.tool.prepare_payment("Course Subscription", 49900, "INR", "EduCorp")
        intent_id = res_prep["data"]["intent_id"]
        # Explicitly decline authorization
        res_auth = self.tool.authorize_payment(intent_id, user_confirm=False)
        self.assertFalse(res_auth["success"])
        self.assertEqual(res_auth["state"], TransactionState.CANCELLED.value)

    # 9. Duplicate transaction detection (Idempotency)
    def test_09_duplicate_transaction_detection(self):
        ref = "DUP_REF_999"
        res1 = self.tool.prepare_payment("Widget A", 150000, "INR", "Shop", merchant_reference=ref)
        res2 = self.tool.prepare_payment("Widget A", 150000, "INR", "Shop", merchant_reference=ref)
        self.assertTrue(res1["success"])
        self.assertTrue(res2["success"])
        self.assertEqual(res1["data"]["intent_id"], res2["data"]["intent_id"])

    # 10. Order creation mock
    def test_10_order_creation_mock(self):
        res_prep = self.tool.prepare_payment("Headphones", 299900, "INR", "AudioShop")
        intent_id = res_prep["data"]["intent_id"]
        self.tool.authorize_payment(intent_id, user_confirm=True)
        res_order = self.tool.create_authorized_order(intent_id, mock=True)
        self.assertTrue(res_order["success"])
        self.assertEqual(res_order["state"], TransactionState.ORDER_CREATED.value)
        self.assertTrue(res_order["data"]["order"]["order_id"].startswith("order_"))

    # 11. Signature verification success
    def test_11_signature_verification_success(self):
        client = RazorpayClient(self.config)
        pid = "pay_test123"
        oid = "order_test123"
        sig = client.verify_payment_signature(pid, oid, "dummy", secret_override="secret")
        # Generate real matching signature
        import hmac, hashlib
        expected_sig = hmac.new(b"secret", f"{oid}|{pid}".encode(), hashlib.sha256).hexdigest()
        is_valid = client.verify_payment_signature(pid, oid, expected_sig, secret_override="secret")
        self.assertTrue(is_valid)

    # 12. Signature verification failure
    def test_12_signature_verification_failure(self):
        client = RazorpayClient(self.config)
        is_valid = client.verify_payment_signature("pay_1", "order_1", "bad_signature_123")
        self.assertFalse(is_valid)

    # 13. Webhook signature success
    def test_13_webhook_signature_success(self):
        client = RazorpayClient(self.config)
        body = b'{"event":"payment.captured"}'
        secret = "wh_secret_123"
        import hmac, hashlib
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        is_valid = client.verify_webhook_signature(body, sig, webhook_secret_override=secret)
        self.assertTrue(is_valid)

    # 14. Webhook signature failure
    def test_14_webhook_signature_failure(self):
        client = RazorpayClient(self.config)
        body = b'{"event":"payment.captured"}'
        is_valid = client.verify_webhook_signature(body, "invalid_sig_xyz")
        self.assertFalse(is_valid)

    # 15. Duplicate webhook handling
    def test_15_duplicate_webhook_handling(self):
        is_new_1 = self.repo.record_webhook_event("evt_1001", "2026-08-22T10:00:00Z")
        is_new_2 = self.repo.record_webhook_event("evt_1001", "2026-08-22T10:00:00Z")
        self.assertTrue(is_new_1)
        self.assertFalse(is_new_2)

    # 16. Payment failure state
    def test_16_payment_failure_state(self):
        res_prep = self.tool.prepare_payment("Failed Item", 10000, "INR", "Store")
        intent_id = res_prep["data"]["intent_id"]
        self.tool.authorize_payment(intent_id, user_confirm=True)
        self.tool.create_authorized_order(intent_id, mock=True)
        res_verify = self.tool.verify_payment(intent_id, "pay_fail", "order_fail", "bad_signature")
        self.assertFalse(res_verify["success"])
        self.assertEqual(res_verify["state"], TransactionState.VERIFICATION_FAILED.value)

    # 17. Successful payment state
    def test_17_successful_payment_state(self):
        res_prep = self.tool.prepare_payment("Success Item", 10000, "INR", "Store")
        intent_id = res_prep["data"]["intent_id"]
        self.tool.authorize_payment(intent_id, user_confirm=True)
        res_order = self.tool.create_authorized_order(intent_id, mock=True)
        order_id = res_order["data"]["order"]["order_id"]
        payment_id = "pay_mock999"

        # Generate valid HMAC signature for mock secret
        import hmac, hashlib
        secret = self.config.key_secret
        sig = hmac.new(secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()

        res_verify = self.tool.verify_payment(intent_id, payment_id, order_id, sig)
        self.assertTrue(res_verify["success"])
        self.assertEqual(res_verify["state"], TransactionState.CAPTURED.value)

    # 18. Secret masking
    def test_18_secret_masking(self):
        masked = PaymentConfig.mask_secret("my_super_secret_key_123")
        self.assertNotIn("super_secret", masked)
        self.assertTrue(masked.startswith("my_"))
        self.assertTrue(masked.endswith("123"))

    # 19. Secret absence from logs / repr
    def test_19_secret_absence_from_logs(self):
        repr_str = str(self.config)
        self.assertNotIn("mock_secret_abcdef123456", repr_str)
        self.assertIn("***", repr_str)

    # 20. Transaction state transitions
    def test_20_transaction_state_transitions(self):
        res_prep = self.tool.prepare_payment("Flow Item", 50000, "INR", "Store")
        intent_id = res_prep["data"]["intent_id"]
        self.assertEqual(res_prep["state"], TransactionState.REQUIRES_AUTHORIZATION.value)

        res_auth = self.tool.authorize_payment(intent_id, user_confirm=True)
        self.assertEqual(res_auth["state"], TransactionState.AUTHORIZED.value)

        res_order = self.tool.create_authorized_order(intent_id, mock=True)
        self.assertEqual(res_order["state"], TransactionState.ORDER_CREATED.value)


if __name__ == "__main__":
    print("=" * 60)
    print("HELIOS Razorpay Payment Foundation Validation Suite")
    print("=" * 60)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.makeSuite(RazorpayValidationSuite))
    if not result.wasSuccessful():
        sys.exit(1)
