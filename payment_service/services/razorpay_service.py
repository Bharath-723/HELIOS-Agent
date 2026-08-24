"""
payment_service/services/razorpay_service.py — Backend Payment Business Service
=================================================================================
Isolated backend service encapsulating Razorpay API calls and TransactionGuard security enforcement.
Keep RAZORPAY_KEY_SECRET contained inside this backend service.
"""

import logging
from typing import Dict, Any, Optional
from core.payments import (
    PaymentConfig, PaymentTool, PaymentRepository, PaymentVerifier
)

log = logging.getLogger("helios.payment_service.razorpay_service")


class RazorpayService:
    def __init__(self, config: Optional[PaymentConfig] = None) -> None:
        self.config = config or PaymentConfig()
        self.repo = PaymentRepository()
        self.tool = PaymentTool(self.config, self.repo)
        self.verifier = PaymentVerifier(self.config, self.tool.client, self.repo, self.tool.guard)

    def prepare_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        description = data.get("description", "HELIOS Order")
        amount = int(data.get("amount", 0))
        currency = data.get("currency", "INR")
        merchant = data.get("merchant_name", "HELIOS Store")
        merchant_ref = data.get("merchant_reference", "")
        meta = data.get("metadata", {})
        return self.tool.prepare_payment(description, amount, currency, merchant, merchant_ref, meta)

    def authorize_transaction(self, intent_id: str, confirm: bool = True) -> Dict[str, Any]:
        return self.tool.authorize_payment(intent_id, user_confirm=confirm)

    def create_order(self, intent_id: str, mock: bool = False) -> Dict[str, Any]:
        return self.tool.create_authorized_order(intent_id, mock=mock)

    def verify_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        intent_id = data.get("intent_id", "")
        pid = data.get("razorpay_payment_id", "")
        oid = data.get("razorpay_order_id", "")
        sig = data.get("razorpay_signature", "")
        return self.tool.verify_payment(intent_id, pid, oid, sig)

    def get_status(self, intent_id: str) -> Dict[str, Any]:
        return self.tool.get_payment_status(intent_id)

    def handle_webhook(self, raw_body: bytes, signature_header: str) -> Dict[str, Any]:
        return self.verifier.process_webhook(raw_body, signature_header)
