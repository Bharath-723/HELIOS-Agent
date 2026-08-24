"""
core/payments/payment_tool.py — High-Level Payment Tool Abstraction
====================================================================
Exposes safe payment actions for HELIOS.
Guarantees structured returns and prevents disclosure of any sensitive credential data.
"""

import uuid
import logging
from typing import Dict, Any, Optional
from core.payments.payment_config import PaymentConfig
from core.payments.payment_models import PaymentIntent, TransactionState
from core.payments.transaction_guard import TransactionGuard
from core.payments.payment_repository import PaymentRepository
from core.payments.razorpay_client import RazorpayClient
from core.payments.payment_verifier import PaymentVerifier
from core.payments.payment_trace import PaymentTraceTracker

log = logging.getLogger("helios.payments.tool")


class PaymentTool:
    def __init__(
        self,
        config: Optional[PaymentConfig] = None,
        repository: Optional[PaymentRepository] = None,
    ) -> None:
        self.config = config or PaymentConfig()
        self.repo = repository or PaymentRepository()
        self.guard = TransactionGuard(self.config)
        self.client = RazorpayClient(self.config)
        self.verifier = PaymentVerifier(self.config, self.client, self.repo, self.guard)

    def prepare_payment(
        self,
        description: str,
        amount: int,  # in paise (e.g. ₹999 = 99900)
        currency: str = "INR",
        merchant_name: str = "Example Merchant",
        merchant_reference: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepares a PaymentIntent in state CREATED or REQUIRES_AUTHORIZATION.
        Checks for idempotent existing transaction first.
        """
        if not self.config.is_valid():
            return {
                "success": False,
                "state": "UNAVAILABLE",
                "message": self.config.get_status_message(),
                "data": None
            }

        if amount <= 0:
            return {
                "success": False,
                "state": TransactionState.FAILED.value,
                "message": "Payment amount must be greater than 0 paise",
                "data": None
            }

        # Idempotency check
        existing = self.repo.find_idempotent_intent(merchant_name, merchant_reference, amount)
        if existing:
            log.info("PaymentTool: Found existing idempotent intent '%s'", existing.intent_id)
            return {
                "success": True,
                "state": existing.status.value,
                "message": "Existing idempotent payment intent returned",
                "data": existing.to_dict()
            }

        intent_id = f"intent_{uuid.uuid4().hex[:14]}"
        intent = PaymentIntent(
            intent_id=intent_id,
            description=description,
            amount=amount,
            currency=currency.upper(),
            merchant_name=merchant_name,
            merchant_reference=merchant_reference or f"ref_{uuid.uuid4().hex[:8]}",
            user_requested=True,
            user_authorized=False,
            status=TransactionState.REQUIRES_AUTHORIZATION,
            metadata=metadata or {}
        )

        trace = PaymentTraceTracker(intent_id)
        trace.record_event("intent_creation", {"amount": amount, "merchant": merchant_name})

        # Check safety amount limits
        if amount > self.config.max_amount_paise:
            intent.status = TransactionState.REQUIRES_ADDITIONAL_AUTHORIZATION
            self.repo.save_intent(intent)
            max_inr = self.config.max_amount_paise / 100.0
            return {
                "success": False,
                "state": TransactionState.REQUIRES_ADDITIONAL_AUTHORIZATION.value,
                "message": f"Payment amount ₹{amount/100.0:,.2f} exceeds maximum allowed threshold ₹{max_inr:,.2f}",
                "data": intent.to_dict()
            }

        self.repo.save_intent(intent)
        return {
            "success": True,
            "state": TransactionState.REQUIRES_AUTHORIZATION.value,
            "message": "Payment prepared successfully. User explicit authorization required.",
            "data": intent.to_dict()
        }

    def authorize_payment(self, intent_id: str, user_confirm: bool = True) -> Dict[str, Any]:
        """
        Explicit out-of-band user authorization step.
        The LLM CANNOT invoke this without explicit user confirmation.
        """
        intent = self.repo.get_intent(intent_id)
        if not intent:
            return {
                "success": False,
                "state": TransactionState.FAILED.value,
                "message": f"Intent '{intent_id}' not found",
                "data": None
            }

        if not user_confirm:
            intent.status = TransactionState.CANCELLED
            self.repo.save_intent(intent)
            return {
                "success": False,
                "state": TransactionState.CANCELLED.value,
                "message": "User declined payment authorization",
                "data": intent.to_dict()
            }

        intent.user_authorized = True
        intent.status = TransactionState.AUTHORIZED
        self.repo.save_intent(intent)

        trace = PaymentTraceTracker(intent_id)
        trace.record_event("user_authorization", {"authorized": True})

        return {
            "success": True,
            "state": TransactionState.AUTHORIZED.value,
            "message": "Transaction authorized by user",
            "data": intent.to_dict()
        }

    def create_authorized_order(self, intent_id: str, mock: bool = False) -> Dict[str, Any]:
        """
        Creates server-side Razorpay Order AFTER TransactionGuard confirms user authorization.
        """
        intent = self.repo.get_intent(intent_id)
        decision = self.guard.can_create_order(intent)

        if not decision.allowed:
            return {
                "success": False,
                "state": decision.state.value if decision.state else TransactionState.FAILED.value,
                "message": decision.reason,
                "data": intent.to_dict() if intent else None
            }

        try:
            order = self.client.create_order(
                amount=intent.amount,
                currency=intent.currency,
                receipt=intent.merchant_reference,
                notes={"intent_id": intent.intent_id, "merchant": intent.merchant_name},
                mock=mock
            )
            self.repo.save_order(intent_id, order)
            trace = PaymentTraceTracker(intent_id)
            trace.record_event("order_creation", {"order_id": order.order_id, "amount": order.amount})

            return {
                "success": True,
                "state": TransactionState.ORDER_CREATED.value,
                "message": f"Razorpay Order '{order.order_id}' created server-side",
                "data": {
                    "intent": intent.to_dict(),
                    "order": order.to_dict()
                }
            }
        except Exception as exc:
            log.error("Failed to create order for intent '%s': %s", intent_id, exc)
            return {
                "success": False,
                "state": TransactionState.FAILED.value,
                "message": f"Order creation failed: {exc}",
                "data": intent.to_dict()
            }

    def verify_payment(
        self,
        intent_id: str,
        razorpay_payment_id: str,
        razorpay_order_id: str,
        razorpay_signature: str
    ) -> Dict[str, Any]:
        """Executes server-side HMAC signature verification."""
        result = self.verifier.verify_payment_response(
            intent_id=intent_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
            razorpay_signature=razorpay_signature
        )

        trace = PaymentTraceTracker(intent_id)
        trace.record_event("signature_verification", {
            "verified": result.verified,
            "payment_id": razorpay_payment_id,
            "order_id": razorpay_order_id
        })

        return {
            "success": result.success,
            "state": result.status.value,
            "message": "Payment verified and captured" if result.success else f"Verification failed: {result.failure_reason}",
            "data": result.to_dict()
        }

    def get_payment_status(self, intent_id: str) -> Dict[str, Any]:
        intent = self.repo.get_intent(intent_id)
        if not intent:
            return {"success": False, "message": "Intent not found", "data": None}
        result = self.repo.get_result(intent_id)
        order = self.repo.get_order(intent.metadata.get("order_id", ""))
        return {
            "success": True,
            "state": intent.status.value,
            "data": {
                "intent": intent.to_dict(),
                "order": order.to_dict() if order else None,
                "result": result.to_dict() if result else None
            }
        }

    def cancel_payment(self, intent_id: str, reason: str = "User cancelled") -> Dict[str, Any]:
        intent = self.repo.get_intent(intent_id)
        if not intent:
            return {"success": False, "message": "Intent not found", "data": None}
        intent.status = TransactionState.CANCELLED
        intent.metadata["cancel_reason"] = reason
        self.repo.save_intent(intent)
        return {
            "success": True,
            "state": TransactionState.CANCELLED.value,
            "message": f"Payment cancelled: {reason}",
            "data": intent.to_dict()
        }
