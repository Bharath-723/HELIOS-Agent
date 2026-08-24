"""
core/commerce/commerce_trace.py — Auditable Commerce Execution Trace
=====================================================================
Logs step-by-step trace records of intent understanding, candidate discovery,
comparison matrix evaluation, recommendation rationale, cost breakdown, authorization,
payment execution, and verification.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

log = logging.getLogger("helios.commerce.trace")


class CommerceTraceTracker:
    """Auditable trace recorder for Agentic Commerce executions."""

    def __init__(self, commerce_id: str) -> None:
        self.commerce_id = commerce_id
        self.events: List[Dict[str, Any]] = []

    def record_step(self, step_name: str, state: str, details: Dict[str, Any]) -> None:
        # Sanitize details to ensure zero secret disclosure
        clean_details = {}
        for k, v in details.items():
            if any(s in k.lower() for s in ("secret", "key_secret", "signature", "auth_token", "password")):
                clean_details[k] = "***REDACTED***"
            else:
                clean_details[k] = v

        entry = {
            "commerce_id": self.commerce_id,
            "step": step_name,
            "state": state,
            "timestamp": datetime.utcnow().isoformat(),
            "details": clean_details
        }
        self.events.append(entry)
        log.info("CommerceTrace [%s] Step: %s | State: %s", self.commerce_id, step_name, state)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commerce_id": self.commerce_id,
            "event_count": len(self.events),
            "trace_log": self.events
        }
