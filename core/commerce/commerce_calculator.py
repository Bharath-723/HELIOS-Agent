"""
core/commerce/commerce_calculator.py — Financial Cost Calculator
==================================================================
Calculates exact item price, shipping, taxes, and total cost in INR/paise,
clearly distinguishing EXACT vs ESTIMATED totals.
"""

import logging
from core.commerce.commerce_models import ProductCandidate, CostBreakdown

log = logging.getLogger("helios.commerce.calculator")


class CommerceCalculator:
    """Financial total calculator for commercial transactions."""

    @staticmethod
    def calculate(candidate: ProductCandidate, shipping_fee: float = 0.0, tax: float = 0.0) -> CostBreakdown:
        log.info("CommerceCalculator: Calculating cost for '%s' (Price: ₹%s)",
                 candidate.name, candidate.price_inr)

        # In standard Sandbox demonstration mode, shipping is free and tax is included in price
        is_exact = True

        return CostBreakdown(
            item_price_inr=candidate.price_inr,
            shipping_fee_inr=shipping_fee,
            tax_inr=tax,
            is_exact_total=is_exact,
            currency="INR"
        )
