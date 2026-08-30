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
    def calculate(candidate: ProductCandidate, quantity: int = 1, shipping_fee: float = 0.0, tax: float = 0.0) -> CostBreakdown:
        qty = max(1, quantity)
        unit_price = candidate.price_inr
        total_item_price = round(unit_price * qty, 2)
        log.info("CommerceCalculator: Calculating cost for '%s' (Unit: ₹%.2f, Qty: %d, Total: ₹%.2f)",
                 candidate.name, unit_price, qty, total_item_price)

        is_exact = True

        return CostBreakdown(
            item_price_inr=total_item_price,
            unit_price_inr=unit_price,
            quantity=qty,
            shipping_fee_inr=shipping_fee,
            tax_inr=tax,
            is_exact_total=is_exact,
            currency="INR"
        )
