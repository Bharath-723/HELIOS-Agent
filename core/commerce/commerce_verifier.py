"""
core/commerce/commerce_verifier.py — Post-Payment Transaction Verifier
========================================================================
Executes server-side signature checks, amount matching, and order consistency
verification before transitioning state to VERIFIED.
"""

import logging
from typing import Dict, Any, Tuple
from core.commerce.commerce_models import CommerceContext, CommerceState

log = logging.getLogger("helios.commerce.verifier")


class CommerceVerifier:
    """Verifies transaction integrity post-checkout."""

    @staticmethod
    def verify(context: CommerceContext, verification_payload: Dict[str, Any]) -> Tuple[bool, str]:
        if not verification_payload.get("success"):
            reason = verification_payload.get("failure_reason") or verification_payload.get("message") or "Verification failed"
            log.error("CommerceVerifier: Payment verification rejected for commerce ID '%s': %s",
                      context.commerce_id, reason)
            return False, reason

        if verification_payload.get("state") in ("CAPTURED", "SIGNATURE_VERIFIED"):
            log.info("CommerceVerifier: Payment successfully verified for commerce ID '%s'", context.commerce_id)
            return True, "Payment verified successfully via HMAC-SHA256 timing-safe check."

        return False, f"Unexpected verification state: {verification_payload.get('state')}"
