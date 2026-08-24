"""
core/payments/payment_models.py — Strongly Typed Models & State Enums
=======================================================================
Isolated payment data structures, transaction state machine enums, and trace objects.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


class TransactionState(str, Enum):
    CREATED = "CREATED"
    REQUIRES_AUTHORIZATION = "REQUIRES_AUTHORIZATION"
    AUTHORIZED = "AUTHORIZED"
    ORDER_CREATED = "ORDER_CREATED"
    CHECKOUT_OPEN = "CHECKOUT_OPEN"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    SIGNATURE_VERIFIED = "SIGNATURE_VERIFIED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    REQUIRES_ADDITIONAL_AUTHORIZATION = "REQUIRES_ADDITIONAL_AUTHORIZATION"


@dataclass
class PaymentIntent:
    intent_id: str
    description: str
    amount: int  # Smallest currency unit (e.g., paise for INR: 99900 = ₹999.00)
    currency: str = "INR"
    merchant_name: str = "Default Merchant"
    merchant_reference: str = ""
    user_requested: bool = True
    user_authorized: bool = False
    status: TransactionState = TransactionState.CREATED
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "description": self.description,
            "amount": self.amount,
            "amount_inr_display": self.amount / 100.0,
            "currency": self.currency,
            "merchant_name": self.merchant_name,
            "merchant_reference": self.merchant_reference,
            "user_requested": self.user_requested,
            "user_authorized": self.user_authorized,
            "status": self.status.value,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class PaymentOrder:
    order_id: str
    amount: int
    currency: str
    receipt: str
    status: str = "created"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "amount": self.amount,
            "currency": self.currency,
            "receipt": self.receipt,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class PaymentResult:
    success: bool
    payment_id: str
    order_id: str
    status: TransactionState
    amount: int
    currency: str
    verified: bool
    failure_reason: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "status": self.status.value if isinstance(self.status, TransactionState) else str(self.status),
            "amount": self.amount,
            "currency": self.currency,
            "verified": self.verified,
            "failure_reason": self.failure_reason,
            "timestamp": self.timestamp,
        }


@dataclass
class TransactionDecision:
    allowed: bool
    reason: str
    state: Optional[TransactionState] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "state": self.state.value if self.state else None,
        }


@dataclass
class PaymentTraceEntry:
    event: str
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        # Clean details to sanitize any secrets just in case
        clean_details = {}
        for k, v in self.details.items():
            if any(s in k.lower() for s in ("secret", "key_secret", "signature", "auth")):
                clean_details[k] = "***REDACTED***"
            else:
                clean_details[k] = v
        return {
            "event": self.event,
            "timestamp": self.timestamp,
            "details": clean_details,
        }


@dataclass
class PaymentContext:
    merchant: str
    product: str
    amount: int  # Smallest currency unit (paise for INR)
    currency: str = "INR"
    merchant_reference: str = ""
    user_constraints: Dict[str, Any] = field(default_factory=dict)
    authorization_required: bool = True
    risk_level: str = "high"
    payment_method: str = "Razorpay"
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    verification_status: str = "PENDING"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "merchant": self.merchant,
            "product": self.product,
            "amount": self.amount,
            "amount_inr_display": self.amount / 100.0,
            "currency": self.currency,
            "merchant_reference": self.merchant_reference,
            "user_constraints": self.user_constraints,
            "authorization_required": self.authorization_required,
            "risk_level": self.risk_level,
            "payment_method": self.payment_method,
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "verification_status": self.verification_status,
        }
