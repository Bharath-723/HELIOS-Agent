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
            
        if features.requires_internet:
            reasons.append("Task requires active internet connection.")
        if features.contains_sensitive_data:
            reasons.append("Task processes sensitive local user credentials/data.")
            
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
            confidence=confidence
        )
