import logging
from datetime import datetime
from core.routing.routing_models import (
    RoutingDecision,
    RoutingFeatures,
    RoutingExplanation,
    ConstraintDecision
)

log = logging.getLogger("helios.routing.explainability")

class ExplainabilityEngine:
    def explain(self, decision: RoutingDecision, features: RoutingFeatures,
                constraint: ConstraintDecision, constraints_triggered: list,
                selected_model: str, confidence: float = 0.0,
                candidate_ranking: list = None,
                capability_mismatches: dict = None,
                selection_margin: float = 0.0) -> RoutingExplanation:
        log.info("explain called: decision=%s, selected_model=%s, confidence=%f", decision, selected_model, confidence)
        
        reasons = []
        if constraint != ConstraintDecision.NONE:
            reasons.append(f"Constraint {constraint.value} triggered: force route selected.")
        else:
            reasons.append("No active constraints. Resolved via utility optimization scoring.")
            
        if features.privacy_score >= 0.70:
            reasons.append("High privacy requirements dictate local confinement.")
        else:
            reasons.append("Low privacy requirements; cloud processing allowed.")
            
        if features.freshness_score >= 0.70:
            reasons.append("Fresh real-time external data is preferred.")
        else:
            reasons.append("Historical/cached local data is sufficient.")

        if features.complexity_score >= 0.70:
            reasons.append("High cognitive complexity task.")
        else:
            reasons.append("Standard complexity; efficient local handling suitable.")
            
        if candidate_ranking:
            reasons.append(f"Model Ranking order: {', '.join(candidate_ranking)}")
        if selection_margin > 0.0:
            reasons.append(f"Selection margin (utility score gap): {selection_margin:.4f}")

        rejected_alts = []
        if candidate_ranking and len(candidate_ranking) > 1:
            for alt in candidate_ranking[1:]:
                mismatch_str = ""
                if capability_mismatches and alt in capability_mismatches:
                    mis = capability_mismatches[alt]
                    mismatch_str = f" [Mismatches -> privacy: {mis.get('privacy', 0.0):.2f}, freshness: {mis.get('freshness', 0.0):.2f}, complexity: {mis.get('complexity', 0.0):.2f}]"
                rejected_alts.append(f"Rejected candidate '{alt}'{mismatch_str}")
        else:
            # Fallback backward-compatible rejection string
            if decision == RoutingDecision.LOCAL:
                rejected_alts.append("Rejected CLOUD alternatives due to cost and latency.")
            else:
                rejected_alts.append("Rejected LOCAL alternatives due to capability and network.")
                
        feature_dict = {
            "privacy_score": features.privacy_score,
            "freshness_score": features.freshness_score,
            "complexity_score": features.complexity_score,
            "requires_internet": features.requires_internet,
            "contains_sensitive_data": features.contains_sensitive_data
        }
        
        return RoutingExplanation(
            decision=decision,
            reasons=reasons,
            feature_values=feature_dict,
            constraints_triggered=constraints_triggered,
            timestamp=datetime.now().isoformat(),
            selected_model=selected_model,
            confidence=confidence,
            rejected_alternatives=rejected_alts
        )
