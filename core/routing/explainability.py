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
                selected_model: str, confidence: float = 0.0) -> RoutingExplanation:
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
            
        rejected_alts = []
        if decision == RoutingDecision.LOCAL:
            cloud_reason = "Rejected CLOUD because:"
            rejs = []
            if features.privacy_score >= 0.70:
                rejs.append("lower privacy satisfaction / privacy penalty")
            if not features.requires_internet:
                rejs.append("internet not required")
            rejs.append("higher operational cost")
            rejected_alts.append(f"{cloud_reason} {', '.join(rejs)}.")
        elif decision == RoutingDecision.CLOUD:
            local_reason = "Rejected LOCAL because:"
            rejs = []
            if features.requires_internet:
                rejs.append("requires internet connectivity")
            if features.complexity_score >= 0.70:
                rejs.append("insufficient local complexity capability")
            rejected_alts.append(f"{local_reason} {', '.join(rejs)}.")
            
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
