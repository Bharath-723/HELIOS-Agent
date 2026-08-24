"""
payment_service/routes/webhooks.py — Webhook Route Handler
===========================================================
Receives and validates Razorpay webhook payloads with immediate HTTP response.
"""

import logging
from typing import Dict, Any
from payment_service.services.razorpay_service import RazorpayService

log = logging.getLogger("helios.payment_service.routes.webhooks")


class WebhookRoutes:
    def __init__(self, service: RazorpayService) -> None:
        self.service = service

    def handle_razorpay_webhook(self, raw_body: bytes, signature_header: str) -> Dict[str, Any]:
        """
        Validates webhook HMAC signature and processes event asynchronously.
        Returns immediate HTTP 200 payload.
        """
        return self.service.handle_webhook(raw_body, signature_header)
