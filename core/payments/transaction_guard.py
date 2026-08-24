"""
core/payments/transaction_guard.py — HELIOS Transaction Guard & Security Enforcement
========================================================================================
Critical security boundary component.
Guarantees that the LLM / Cognitive Planning system NEVER directly executes or authorizes payments.
All financial transactions require explicit, out-of-band user authorization.
"""

import logging
from typing import Optional
from core.payments.payment_config import PaymentConfig
from core.payments.payment_models import (
    PaymentIntent, PaymentOrder, PaymentResult,
    TransactionState, TransactionDecision
)

log = logging.getLogger("helios.payments.guard")


class TransactionGuard:
    def __init__(self, config: Optional[PaymentConfig] = None) -> None:
        self.config = config or PaymentConfig()

    def can_create_order(self, intent: Optional[PaymentIntent]) -> TransactionDecision:
        """
        Validates whether a Razorpay order can be created server-side for this intent.
        Requires valid intent fields AND explicit user authorization.
        """
        if intent is None:
            return TransactionDecision(allowed=False, reason="Payment intent does not exist", state=TransactionState.FAILED)

        if not intent.intent_id:
            return TransactionDecision(allowed=False, reason="Invalid payment intent ID", state=TransactionState.FAILED)

        if not intent.merchant_name:
            return TransactionDecision(allowed=False, reason="Merchant name is missing", state=TransactionState.FAILED)

        if intent.amount <= 0:
            return TransactionDecision(allowed=False, reason="Invalid payment amount (must be > 0)", state=TransactionState.FAILED)

        if not intent.currency:
            return TransactionDecision(allowed=False, reason="Currency is missing", state=TransactionState.FAILED)

        if intent.status in (TransactionState.CAPTURED, TransactionState.PAYMENT_RECEIVED):
            return TransactionDecision(allowed=False, reason="Payment has already been completed", state=intent.status)

        # Check safety amount limits
        if intent.amount > self.config.max_amount_paise:
            max_inr = self.config.max_amount_paise / 100.0
            req_inr = intent.amount / 100.0
            return TransactionDecision(
                allowed=False,
                reason=f"Payment amount ₹{req_inr:,.2f} exceeds maximum allowed safety threshold of ₹{max_inr:,.2f}",
                state=TransactionState.REQUIRES_ADDITIONAL_AUTHORIZATION
            )

        # CRITICAL SECURITY RULE: User MUST have explicitly authorized
        if not intent.user_authorized:
            return TransactionDecision(
                allowed=False,
                reason="Explicit user authorization required to proceed with payment",
                state=TransactionState.REQUIRES_AUTHORIZATION
            )

        return TransactionDecision(allowed=True, reason="Order creation authorized by user policy", state=TransactionState.AUTHORIZED)

    def can_open_checkout(self, intent: Optional[PaymentIntent], order: Optional[PaymentOrder]) -> TransactionDecision:
        """Validates whether client checkout can be opened for the specified order."""
        if intent is None or order is None:
            return TransactionDecision(allowed=False, reason="Missing intent or order reference")

        if not intent.user_authorized:
            return TransactionDecision(allowed=False, reason="Explicit user authorization required for checkout launch")

        if intent.amount != order.amount:
            return TransactionDecision(allowed=False, reason="Security violation: Intent amount does not match Order amount")

        if intent.status in (TransactionState.CAPTURED, TransactionState.PAYMENT_RECEIVED):
            return TransactionDecision(allowed=False, reason="Transaction already completed")

        return TransactionDecision(allowed=True, reason="Checkout launch allowed", state=TransactionState.CHECKOUT_OPEN)

    def can_verify_payment(self, intent: Optional[PaymentIntent], payment_id: str, order_id: str) -> TransactionDecision:
        """Validates input parameters before initiating server-side signature verification."""
        if intent is None:
            return TransactionDecision(allowed=False, reason="Payment intent does not exist")

        if not payment_id or not payment_id.startswith("pay_"):
            return TransactionDecision(allowed=False, reason="Invalid or missing Razorpay payment_id")

        if not order_id or not order_id.startswith("order_"):
            return TransactionDecision(allowed=False, reason="Invalid or missing Razorpay order_id")

        # Verify that order_id matches the trusted intent metadata
        trusted_order_id = intent.metadata.get("order_id")
        if trusted_order_id and trusted_order_id != order_id:
            return TransactionDecision(
                allowed=False,
                reason=f"Security Alert: Client order ID '{order_id}' does not match trusted server order ID '{trusted_order_id}'"
            )

        return TransactionDecision(allowed=True, reason="Payment verification allowed")

    def can_complete_transaction(self, intent: Optional[PaymentIntent], result: Optional[PaymentResult]) -> TransactionDecision:
        """Validates whether a transaction state can transition to CAPTURED / COMPLETED."""
        if intent is None or result is None:
            return TransactionDecision(allowed=False, reason="Missing intent or verification result")

        if not result.verified or not result.success:
            return TransactionDecision(allowed=False, reason="Cannot complete transaction: Signature verification failed")

        return TransactionDecision(allowed=True, reason="Transaction completion authorized", state=TransactionState.CAPTURED)
