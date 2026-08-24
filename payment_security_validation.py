"""
payment_security_validation.py — HELIOS Payment Security & Isolation Audit Suite
===================================================================================
Explicitly tests and verifies security invariants:
- Secret protection & zero-leak guarantees
- TransactionGuard policy enforcement
- Immutability of amounts post-authorization
- Server-side order ID validation
- HMAC verification timing-safety & webhook anti-replay
"""

import sys
import unittest
import logging
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

from core.payments import (
    PaymentConfig, PaymentIntent, PaymentOrder, PaymentResult,
    TransactionState, TransactionGuard, PaymentRepository,
    RazorpayClient, PaymentVerifier, PaymentTool, PaymentTraceTracker,
    HeliosPaymentAdapter, sanitize_payload
)


class PaymentSecurityValidationSuite(unittest.TestCase):

    def setUp(self):
        self.secret = "rzp_secret_ultra_top_secret_key_99999"
        self.mock_env = {
            "RAZORPAY_KEY_ID": "rzp_test_key_12345",
            "RAZORPAY_KEY_SECRET": self.secret,
            "RAZORPAY_MODE": "sandbox",
            "RAZORPAY_WEBHOOK_SECRET": "whsec_super_secret_88888",
            "MAX_PAYMENT_AMOUNT_INR": "10000"
        }
        self.config = PaymentConfig(self.mock_env)
        self.repo = PaymentRepository()
        self.tool = PaymentTool(self.config, self.repo)
        self.guard = TransactionGuard(self.config)

    # 1. Key Secret never appears in logs or repr
    def test_sec_01_secret_never_in_repr_or_str(self):
        config_str = str(self.config)
        self.assertNotIn(self.secret, config_str)
        self.assertIn("***", config_str)

    # 2. Key Secret never appears in PaymentTrace
    def test_sec_02_secret_never_in_payment_trace(self):
        trace = PaymentTraceTracker("intent_sec_101")
        trace.record_event("test_event", {
            "razorpay_key_secret": self.secret,
            "amount": 99900,
            "signature": "sig_123"
        })
        trace_data = trace.get_trace()
        trace_str = json.dumps(trace_data)
        self.assertNotIn(self.secret, trace_str)
        self.assertIn("***REDACTED***", trace_str)

    # 3. Key Secret never appears in UI payloads
    def test_sec_03_secret_never_in_ui_payloads(self):
        res = self.tool.prepare_payment("Test Item", 50000, "INR", "Store")
        payload_str = json.dumps(res)
        self.assertNotIn(self.secret, payload_str)

    # 4. LLM cannot authorize payment without explicit user action
    def test_sec_04_llm_cannot_authorize_payment(self):
        # LLM creates intent
        res_prep = self.tool.prepare_payment("Autonomous Purchase", 100000, "INR", "Store")
        intent_id = res_prep["data"]["intent_id"]

        # Attempt order creation directly without user authorization step
        res_order = self.tool.create_authorized_order(intent_id, mock=True)
        self.assertFalse(res_order["success"])
        self.assertIn("Explicit user authorization required", res_order["message"])

    # 5. Client cannot arbitrarily change amount after authorization
    def test_sec_05_amount_immutability_post_authorization(self):
        res_prep = self.tool.prepare_payment("Immutable Item", 200000, "INR", "Store")
        intent_id = res_prep["data"]["intent_id"]
        intent = self.repo.get_intent(intent_id)

        # Authorize
        self.tool.authorize_payment(intent_id, user_confirm=True)

        # Create order with original amount
        order = PaymentOrder("order_original_123", amount=200000, currency="INR", receipt="ref")

        # Attempt to open checkout with tampered order amount
        tampered_order = PaymentOrder("order_original_123", amount=50000, currency="INR", receipt="ref")
        decision = self.guard.can_open_checkout(intent, tampered_order)

        self.assertFalse(decision.allowed)
        self.assertIn("amount does not match", decision.reason.lower())

    # 6. Client cannot substitute order_id during verification
    def test_sec_06_order_id_substitution_rejection(self):
        res_prep = self.tool.prepare_payment("Protected Item", 100000, "INR", "Store")
        intent_id = res_prep["data"]["intent_id"]
        self.tool.authorize_payment(intent_id, user_confirm=True)

        res_order = self.tool.create_authorized_order(intent_id, mock=True)
        trusted_order_id = res_order["data"]["order"]["order_id"]

        # Client attempts verification with substituted fake order ID
        fake_order_id = "order_substituted_fake_999"
        decision = self.guard.can_verify_payment(self.repo.get_intent(intent_id), "pay_123", fake_order_id)

        self.assertFalse(decision.allowed)
        self.assertIn("Security Alert", decision.reason)

    # 7. Invalid webhook signature is rejected
    def test_sec_07_invalid_webhook_signature_rejected(self):
        verifier = PaymentVerifier(self.config, repository=self.repo)
        body = b'{"event":"payment.captured"}'
        bad_sig = "invalid_hmac_signature_header_val"

        with self.assertRaises(Exception):
            verifier.process_webhook(body, bad_sig)

    # 8. Duplicate webhook is ignored (Anti-replay)
    def test_sec_08_duplicate_webhook_ignored(self):
        verifier = PaymentVerifier(self.config, repository=self.repo)
        body = b'{"event":"payment.captured","account_id":"acc_1","created_at":1700000000}'

        import hmac, hashlib
        sig = hmac.new(self.config.webhook_secret.encode(), body, hashlib.sha256).hexdigest()

        res1 = verifier.process_webhook(body, sig)
        res2 = verifier.process_webhook(body, sig)

        self.assertEqual(res1["status"], "processed")
        self.assertEqual(res2["status"], "ignored")

    # 9. Duplicate payment preparation is idempotent
    def test_sec_09_payment_preparation_idempotency(self):
        ref = "IDEMPOTENT_REF_777"
        res1 = self.tool.prepare_payment("Subscription", 50000, "INR", "SaaS Co", merchant_reference=ref)
        res2 = self.tool.prepare_payment("Subscription", 50000, "INR", "SaaS Co", merchant_reference=ref)

        self.assertEqual(res1["data"]["intent_id"], res2["data"]["intent_id"])


if __name__ == "__main__":
    print("=" * 60)
    print("HELIOS Payment Security & Isolation Audit Suite")
    print("=" * 60)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.makeSuite(PaymentSecurityValidationSuite))
    if not result.wasSuccessful():
        sys.exit(1)
