"""
core/payments/razorpay_client.py — Isolated Razorpay API Wrapper & Signature Verification
==========================================================================================
Handles all direct communication with Razorpay REST APIs and HMAC-SHA256 signature checks.
Amounts are strictly handled in the smallest currency unit (paise for INR).
"""

import hmac
import hashlib
import requests
import logging
import uuid
from typing import Dict, Any, Optional
from core.payments.payment_config import PaymentConfig
from core.payments.payment_models import PaymentOrder
from core.payments.exceptions import PaymentOrderException, PaymentVerificationException

log = logging.getLogger("helios.payments.razorpay_client")

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"


class RazorpayClient:
    def __init__(self, config: Optional[PaymentConfig] = None) -> None:
        self.config = config or PaymentConfig()

    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
        mock: bool = False
    ) -> PaymentOrder:
        """
        Creates a server-side Razorpay Order.
        Amount must be in smallest currency unit (e.g., paise for INR: 99900 = ₹999.00).
        """
        if amount <= 0:
            raise PaymentOrderException("Amount must be greater than 0 paise")

        receipt_str = receipt or f"rcpt_{uuid.uuid4().hex[:12]}"
        payload = {
            "amount": amount,
            "currency": currency.upper(),
            "receipt": receipt_str,
            "notes": notes or {},
        }

        # Mock fallback if credentials are test placeholders or mock requested
        if mock or not self.config.is_valid() or self.config.key_id.startswith("rzp_test_mock"):
            mock_order_id = f"order_{uuid.uuid4().hex[:14]}"
            log.info("RazorpayClient [SANDBOX MOCK]: Created Order %s (Amount: %d paise)", mock_order_id, amount)
            return PaymentOrder(
                order_id=mock_order_id,
                amount=amount,
                currency=currency.upper(),
                receipt=receipt_str,
                status="created"
            )

        try:
            resp = requests.post(
                f"{RAZORPAY_API_BASE}/orders",
                auth=(self.config.key_id, self.config.key_secret),
                json=payload,
                timeout=10
            )
            if resp.status_code != 200:
                log.error("Razorpay API Error [%d]: %s", resp.status_code, resp.text)
                raise PaymentOrderException(f"Razorpay order creation failed: {resp.text}")

            data = resp.json()
            return PaymentOrder(
                order_id=data["id"],
                amount=data["amount"],
                currency=data["currency"],
                receipt=data.get("receipt", receipt_str),
                status=data.get("status", "created")
            )
        except requests.RequestException as req_ex:
            log.error("Razorpay network request error: %s", req_ex)
            raise PaymentOrderException(f"Network error during Razorpay order creation: {req_ex}")

    def fetch_order(self, order_id: str, mock_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetches order status from Razorpay."""
        if mock_data:
            return mock_data

        if not self.config.is_valid() or self.config.key_id.startswith("rzp_test_mock"):
            return {
                "id": order_id,
                "amount": 99900,
                "currency": "INR",
                "status": "created",
                "attempts": 0
            }

        try:
            resp = requests.get(
                f"{RAZORPAY_API_BASE}/orders/{order_id}",
                auth=(self.config.key_id, self.config.key_secret),
                timeout=10
            )
            if resp.status_code != 200:
                raise PaymentOrderException(f"Failed to fetch order '{order_id}': {resp.text}")
            return resp.json()
        except requests.RequestException as exc:
            raise PaymentOrderException(f"Network error fetching order '{order_id}': {exc}")

    def fetch_payment(self, payment_id: str, mock_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetches payment details from Razorpay."""
        if mock_data:
            return mock_data

        if not self.config.is_valid() or self.config.key_id.startswith("rzp_test_mock"):
            return {
                "id": payment_id,
                "entity": "payment",
                "amount": 99900,
                "currency": "INR",
                "status": "captured",
                "order_id": "order_mock123"
            }

        try:
            resp = requests.get(
                f"{RAZORPAY_API_BASE}/payments/{payment_id}",
                auth=(self.config.key_id, self.config.key_secret),
                timeout=10
            )
            if resp.status_code != 200:
                raise PaymentOrderException(f"Failed to fetch payment '{payment_id}': {resp.text}")
            return resp.json()
        except requests.RequestException as exc:
            raise PaymentOrderException(f"Network error fetching payment '{payment_id}': {exc}")

    def verify_payment_signature(
        self,
        payment_id: str,
        order_id: str,
        signature: str,
        secret_override: Optional[str] = None
    ) -> bool:
        """
        Verifies Razorpay Checkout signature using HMAC-SHA256 with timing-safe comparison.
        Payload format: "{order_id}|{payment_id}"
        """
        secret = secret_override or self.config.key_secret
        if not secret:
            log.error("Signature verification failed: Key secret not set.")
            return False

        if not payment_id or not order_id or not signature:
            return False

        message = f"{order_id}|{payment_id}".encode("utf-8")
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            message,
            hashlib.sha256
        ).hexdigest()

        # Timing-safe comparison
        is_valid = hmac.compare_digest(expected_sig, signature)
        if not is_valid:
            log.warning("Signature mismatch for Order '%s' / Payment '%s'", order_id, payment_id)
        return is_valid

    def verify_webhook_signature(
        self,
        body_bytes: bytes,
        signature: str,
        webhook_secret_override: Optional[str] = None
    ) -> bool:
        """
        Verifies Razorpay Webhook signature using HMAC-SHA256.
        """
        secret = webhook_secret_override or self.config.webhook_secret
        if not secret:
            log.error("Webhook signature verification failed: Webhook secret not set.")
            return False

        if not body_bytes or not signature:
            return False

        expected_sig = hmac.new(
            secret.encode("utf-8"),
            body_bytes,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature)
