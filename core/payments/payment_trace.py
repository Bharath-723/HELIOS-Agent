"""
core/payments/payment_trace.py — Auditable Payment Trace Tracking
===================================================================
Tracks full payment lifecycle events while strictly enforcing secret masking.
No raw credentials or secrets are ever recorded in traces or output payloads.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from core.payments.payment_models import PaymentTraceEntry

log = logging.getLogger("helios.payments.trace")

_SENSITIVE_KEYS = {
    "key_secret", "razorpay_key_secret", "secret", "webhook_secret",
    "signature", "razorpay_signature", "authorization", "auth_token", "password"
}


def sanitize_payload(data: Any) -> Any:
    """Recursively redacts any sensitive keys from data structures."""
    if isinstance(data, dict):
        clean = {}
        for k, v in data.items():
            if any(s in str(k).lower() for s in _SENSITIVE_KEYS):
                clean[k] = "***REDACTED***"
            else:
                clean[k] = sanitize_payload(v)
        return clean
    elif isinstance(data, list):
        return [sanitize_payload(item) for item in data]
    elif isinstance(data, str):
        # Additional safety scan if string contains key patterns
        if "rzp_test_secret" in data or "rzp_live_secret" in data:
            return "***REDACTED_SECRET***"
        return data
    return data


class PaymentTraceTracker:
    def __init__(self, intent_id: str) -> None:
        self.intent_id = intent_id
        self._entries: List[PaymentTraceEntry] = []

    def record_event(self, event_name: str, details: Dict[str, Any] = None) -> None:
        clean_details = sanitize_payload(details or {})
        entry = PaymentTraceEntry(
            event=event_name,
            timestamp=datetime.utcnow().isoformat(),
            details=clean_details
        )
        self._entries.append(entry)
        log.debug("PaymentTrace [%s] | %s | %s", self.intent_id, event_name, clean_details)

    def get_trace(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._entries]

    def clear(self) -> None:
        self._entries.clear()
