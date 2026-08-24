"""
core/payments/payment_verifier.py — Server-Side Payment Verification & Webhook Processor
========================================================================================
Executes trusted server-side signature checks and handles Razorpay webhook event processing.
"""

import json
import logging
from typing import Dict, Any, Optional
from core.payments.payment_config import PaymentConfig
from core.payments.razorpay_client import RazorpayClient
from core.payments.transaction_guard import TransactionGuard
from core.payments.payment_repository import PaymentRepository
from core.payments.payment_models import (
    PaymentResult, TransactionState
)
from core.payments.exceptions import PaymentVerificationException

log = logging.getLogger("helios.payments.verifier")


class PaymentVerifier:
    def __init__(
        self,
        config: Optional[PaymentConfig] = None,
        client: Optional[RazorpayClient] = None,
        repository: Optional[PaymentRepository] = None,
        guard: Optional[TransactionGuard] = None,
    ) -> None:
        self.config = config or PaymentConfig()
        self.client = client or RazorpayClient(self.config)
        self.repo = repository or PaymentRepository()
        self.guard = guard or TransactionGuard(self.config)

    def verify_payment_response(
        self,
        intent_id: str,
        razorpay_payment_id: str,
        razorpay_order_id: str,
        razorpay_signature: str
    ) -> PaymentResult:
        """
        Server-side signature verification for Razorpay Checkout response.
        Ensures order_id matches trusted intent metadata and signature is HMAC-SHA256 valid.
        """
        intent = self.repo.get_intent(intent_id)
        if not intent:
            log.error("Payment verification failed: Intent '%s' not found.", intent_id)
            return PaymentResult(
                success=False,
                payment_id=razorpay_payment_id,
                order_id=razorpay_order_id,
                status=TransactionState.VERIFICATION_FAILED,
                amount=0,
                currency="INR",
                verified=False,
                failure_reason=f"Payment intent '{intent_id}' not found"
            )

        # TransactionGuard verification permissions check
        decision = self.guard.can_verify_payment(intent, razorpay_payment_id, razorpay_order_id)
        if not decision.allowed:
            log.error("TransactionGuard blocked verification: %s", decision.reason)
            result = PaymentResult(
                success=False,
                payment_id=razorpay_payment_id,
                order_id=razorpay_order_id,
                status=TransactionState.VERIFICATION_FAILED,
                amount=intent.amount,
                currency=intent.currency,
                verified=False,
                failure_reason=decision.reason
            )
            self.repo.save_result(intent_id, result)
            return result

        # Perform HMAC-SHA256 Signature Verification
        is_valid_sig = self.client.verify_payment_signature(
            payment_id=razorpay_payment_id,
            order_id=razorpay_order_id,
            signature=razorpay_signature
        )

        if not is_valid_sig:
            log.warning("HMAC Signature Verification Failed for Intent '%s'", intent_id)
            result = PaymentResult(
                success=False,
                payment_id=razorpay_payment_id,
                order_id=razorpay_order_id,
                status=TransactionState.VERIFICATION_FAILED,
                amount=intent.amount,
                currency=intent.currency,
                verified=False,
                failure_reason="HMAC-SHA256 signature verification failed"
            )
            self.repo.save_result(intent_id, result)
            return result

        # Transition state: SIGNATURE_VERIFIED -> CAPTURED
        intent.status = TransactionState.SIGNATURE_VERIFIED
        result = PaymentResult(
            success=True,
            payment_id=razorpay_payment_id,
            order_id=razorpay_order_id,
            status=TransactionState.CAPTURED,
            amount=intent.amount,
            currency=intent.currency,
            verified=True,
            failure_reason=None
        )
        self.repo.save_result(intent_id, result)
        log.info("Payment Verification SUCCESS for Intent '%s' [PaymentID: %s]", intent_id, razorpay_payment_id)
        return result

    def process_webhook(
        self,
        raw_body: bytes,
        signature_header: str
    ) -> Dict[str, Any]:
        """
        Validates and processes incoming Razorpay Webhook events.
        Idempotent & non-blocking structure.
        """
        if not self.client.verify_webhook_signature(raw_body, signature_header):
            log.error("Webhook processing rejected: Invalid HMAC signature header.")
            raise PaymentVerificationException("Invalid Razorpay webhook signature")

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            raise PaymentVerificationException(f"Invalid JSON webhook body: {exc}")

        event_id = payload.get("account_id", "") + "_" + str(payload.get("created_at", ""))
        event_name = payload.get("event", "unknown")

        # Duplicate event idempotency check
        is_new = self.repo.record_webhook_event(event_id, str(payload.get("created_at")))
        if not is_new:
            log.info("Duplicate Webhook event '%s' ignored.", event_id)
            return {"status": "ignored", "reason": "Duplicate webhook event"}

        # Extract payment payload entity
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id", "")
        payment_id = payment_entity.get("id", "")

        log.info("Webhook Event Received | Event: '%s' | Order: '%s' | Payment: '%s'", event_name, order_id, payment_id)

        return {
            "status": "processed",
            "event": event_name,
            "order_id": order_id,
            "payment_id": payment_id,
        }
