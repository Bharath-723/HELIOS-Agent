"""
payment_service/routes/payments.py — Backend Payment Route Handlers
=====================================================================
Isolated payment API endpoints for prepare, authorize, order creation, and verification.
"""

import logging
from typing import Dict, Any
from payment_service.services.razorpay_service import RazorpayService

log = logging.getLogger("helios.payment_service.routes.payments")


class PaymentRoutes:
    def __init__(self, service: RazorpayService) -> None:
        self.service = service

    def handle_prepare(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.service.prepare_transaction(payload)

    def handle_authorize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        intent_id = payload.get("intent_id", "")
        confirm = bool(payload.get("confirm", True))
        return self.service.authorize_transaction(intent_id, confirm)

    def handle_create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        intent_id = payload.get("intent_id", "")
        mock = bool(payload.get("mock", False))
        return self.service.create_order(intent_id, mock=mock)

    def handle_verify(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.service.verify_payment(payload)

    def handle_get_status(self, intent_id: str) -> Dict[str, Any]:
        return self.service.get_status(intent_id)
