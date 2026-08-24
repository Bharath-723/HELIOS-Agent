"""
core/commerce/commerce_authorization.py — Human Authorization Policy Guard
=============================================================================
Enforces hard safety policy boundaries requiring explicit human button interaction
before financial movement, verifying amount immutability and threshold limits.
"""

import logging
from typing import Dict, Any, Tuple
from core.commerce.commerce_models import CommerceContext, CommerceState
from core.payments import TransactionGuard, TransactionState

log = logging.getLogger("helios.commerce.authorization")


class CommerceAuthorizationGuard:
    """Enforces explicit human authorization policy guard for Commerce workflows."""

    @staticmethod
    def validate_authorization_request(context: CommerceContext) -> Tuple[bool, str]:
        if not context.recommendation or not context.cost:
            return False, "Invalid context: Missing recommendation or cost breakdown."

        # Safety threshold check (₹10,000 max)
        if context.cost.total_inr > 10000.0:
            return False, f"Additional authorization required: Total ₹{context.cost.total_inr:,.2f} exceeds safety threshold of ₹10,000.00."

        return True, "Authorization request valid. Awaiting explicit user button interaction."

    @staticmethod
    def verify_amount_immutability(original_amount_paise: int, post_auth_amount_paise: int) -> bool:
        if original_amount_paise != post_auth_amount_paise:
            log.error("SECURITY ALERT: Amount altered post-authorization! (Original: %d, New: %d)",
                      original_amount_paise, post_auth_amount_paise)
            return False
        return True

    @staticmethod
    def revalidate_price(context: CommerceContext, current_live_price_inr: float) -> Tuple[bool, str]:
        """
        Revalidates live product price immediately prior to order creation.
        If price changed (e.g. ₹1,799 -> ₹1,999), blocks payment and invalidates authorization.
        """
        if not context.cost:
            return False, "Missing cost context for price revalidation."

        original_price = context.cost.item_price_inr
        if abs(original_price - current_live_price_inr) > 0.01:
            log.error("PRICE CHANGE DETECTED: Original: ₹%.2f, Current Live: ₹%.2f",
                      original_price, current_live_price_inr)
            context.state = CommerceState.TRANSACTION_FAILED
            context.error_message = (
                f"Price changed since research! Original price: ₹{original_price:,.2f}, "
                f"New live price: ₹{current_live_price_inr:,.2f}. Transaction cancelled for safety."
            )
            return False, context.error_message

        return True, "Price revalidation passed."
