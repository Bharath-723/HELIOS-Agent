"""
payment_service/app.py — HELIOS Isolated Payment Backend Service App
======================================================================
Standalone backend service for payment processing, order creation, signature verification,
and Razorpay webhook callbacks.
"""

import json
import logging
from typing import Dict, Any, Tuple
from payment_service.services.razorpay_service import RazorpayService
from payment_service.routes.payments import PaymentRoutes
from payment_service.routes.webhooks import WebhookRoutes
from core.payments import PaymentConfig

log = logging.getLogger("helios.payment_service.app")


class PaymentServiceApp:
    def __init__(self, config: PaymentConfig = None) -> None:
        self.config = config or PaymentConfig()
        self.service = RazorpayService(self.config)
        self.payment_routes = PaymentRoutes(self.service)
        self.webhook_routes = WebhookRoutes(self.service)

    def dispatch_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body_bytes: bytes
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Dispatches HTTP requests to appropriate payment or webhook handler.
        Returns (http_status_code, response_dict).
        """
        method = method.upper().strip()
        path = path.strip()

        # Parse JSON body if present
        json_body = {}
        if body_bytes and method in ("POST", "PUT"):
            try:
                json_body = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                pass

        log.debug("PaymentServiceApp Request | %s %s", method, path)

        if method == "POST" and path in ("/payments/prepare", "/payments/prepare/"):
            res = self.payment_routes.handle_prepare(json_body)
            status = 200 if res.get("success") else 400
            return status, res

        elif method == "POST" and path in ("/payments/authorize", "/payments/authorize/"):
            res = self.payment_routes.handle_authorize(json_body)
            status = 200 if res.get("success") else 400
            return status, res

        elif method == "POST" and path in ("/payments/order", "/payments/order/"):
            res = self.payment_routes.handle_create_order(json_body)
            status = 200 if res.get("success") else 400
            return status, res

        elif method == "POST" and path in ("/payments/verify", "/payments/verify/"):
            res = self.payment_routes.handle_verify(json_body)
            status = 200 if res.get("success") else 400
            return status, res

        elif method == "GET" and path.startswith("/payments/"):
            intent_id = path.split("/payments/")[1].strip("/")
            res = self.payment_routes.handle_get_status(intent_id)
            status = 200 if res.get("success") else 404
            return status, res

        elif method == "POST" and path in ("/webhooks/razorpay", "/webhooks/razorpay/"):
            sig_header = headers.get("X-Razorpay-Signature", headers.get("x-razorpay-signature", ""))
            try:
                res = self.webhook_routes.handle_razorpay_webhook(body_bytes, sig_header)
                return 200, res
            except Exception as exc:
                log.error("Webhook processing error: %s", exc)
                return 400, {"status": "failed", "reason": str(exc)}

        return 404, {"error": f"Endpoint '{method} {path}' not found"}


def create_app(config: PaymentConfig = None) -> PaymentServiceApp:
    return PaymentServiceApp(config)
