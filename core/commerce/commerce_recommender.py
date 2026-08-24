"""
core/commerce/commerce_recommender.py — Explainable Recommendation Engine
===========================================================================
Formulates an explainable recommendation containing selected product, reason,
alternative, tradeoffs, and confidence score.
"""

import logging
from typing import List, Optional
from core.commerce.commerce_models import (
    ProductCandidate, ComparisonTable, RecommendationResult, CommerceIntent
)

log = logging.getLogger("helios.commerce.recommender")


class CommerceRecommender:
    """Formulates explainable recommendation decisions."""

    @staticmethod
    def recommend(intent: CommerceIntent, comparison: ComparisonTable) -> Optional[RecommendationResult]:
        if not comparison.candidates:
            return None

        best_id = comparison.best_candidate_id or comparison.candidates[0].candidate_id
        selected = next((c for c in comparison.candidates if c.candidate_id == best_id), comparison.candidates[0])

        # Find secondary alternative
        alternatives = [c for c in comparison.candidates if c.candidate_id != selected.candidate_id]
        alt = alternatives[0] if alternatives else None

        # Build transparent rationale
        reasons = []
        if intent.budget_limit_inr:
            reasons.append(f"It fits comfortably within your budget of ₹{intent.budget_limit_inr:,.2f} at ₹{selected.price_inr:,.2f}.")
        reasons.append(f"It holds a high customer rating of {selected.rating}★ with {selected.review_count} verified reviews.")
        if selected.pros:
            reasons.append(f"Key strengths: {', '.join(selected.pros[:2])}.")

        reason_str = " ".join(reasons)

        tradeoffs = []
        if selected.cons:
            tradeoffs.append(f"Trade-off: {', '.join(selected.cons)}.")
        if alt:
            tradeoffs.append(f"Alternative consideration: {alt.name} is available for ₹{alt.price_inr:,.2f}.")

        return RecommendationResult(
            selected_candidate=selected,
            reason=reason_str,
            alternative=alt,
            tradeoffs=tradeoffs,
            confidence_score=selected.confidence
        )
