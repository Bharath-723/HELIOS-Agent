import logging
from core.routing.routing_models import (
    RoutingContext,
    RoutingFeatures,
    RoutingDecision,
    ConstraintDecision
)

log = logging.getLogger("helios.routing.decision_engine")

class DecisionEngine:
    def make_decision(self, context: RoutingContext, features: RoutingFeatures,
                      constraint: ConstraintDecision, scores: dict) -> RoutingDecision:
        log.info("make_decision called: constraint=%s", constraint)
        
        if constraint == ConstraintDecision.FORCE_LOCAL:
            return RoutingDecision.LOCAL
        elif constraint == ConstraintDecision.FORCE_CLOUD:
            return RoutingDecision.CLOUD
            
        if features.complexity_score >= 0.80:
            return RoutingDecision.CLOUD
        if features.requires_internet:
            return RoutingDecision.CLOUD
            
        return RoutingDecision.LOCAL
