"""
core/commerce/commerce_comparator.py — Deterministic Comparison Engine
========================================================================
Generates structured ComparisonTable matrix comparing candidates side-by-side
across budget, features, pros, cons, and constraint match scores.
"""

import logging
from typing import List, Optional
from core.commerce.commerce_models import ProductCandidate, ComparisonTable, CommerceIntent

log = logging.getLogger("helios.commerce.comparator")


class CommerceComparator:
    """Deterministic candidate comparison matrix builder."""

    @staticmethod
    def compare(intent: CommerceIntent, candidates: List[ProductCandidate]) -> ComparisonTable:
        log.info("CommerceComparator: Comparing %d candidates for '%s'",
                 len(candidates), intent.target_item)

        if not candidates:
            return ComparisonTable(
                target_item=intent.target_item,
                budget_limit_inr=intent.budget_limit_inr,
                candidates=[],
                best_candidate_id=None,
                evaluation_matrix={}
            )

        matrix = {}
        best_id = None
        best_score = -1.0

        for c in candidates:
            # Score formula: Rating weight (40%) + Constraint match (40%) + Value factor (20%)
            match_ratio = len(c.constraints_satisfied) / max(1, len(c.constraints_satisfied) + len(c.constraints_violated))
            rating_norm = c.rating / 5.0

            # Value factor: Budget ratio if budget specified
            value_factor = 1.0
            if intent.budget_limit_inr and intent.budget_limit_inr > 0:
                value_factor = 1.0 - (c.price_inr / (intent.budget_limit_inr * 1.5))

            composite_score = round((rating_norm * 0.4) + (match_ratio * 0.4) + (value_factor * 0.2), 3)

            matrix[c.candidate_id] = {
                "name": c.name,
                "price": f"₹{c.price_inr:,.2f}",
                "merchant": c.merchant,
                "rating": f"{c.rating}★",
                "match_score": composite_score,
                "constraints_met": len(c.constraints_satisfied),
                "pros_count": len(c.pros),
                "cons_count": len(c.cons)
            }

            if composite_score > best_score:
                best_score = composite_score
                best_id = c.candidate_id

        return ComparisonTable(
            target_item=intent.target_item,
            budget_limit_inr=intent.budget_limit_inr,
            candidates=candidates,
            best_candidate_id=best_id,
            evaluation_matrix=matrix
        )
