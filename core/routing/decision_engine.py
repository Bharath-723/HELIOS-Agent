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
            
        local_val = scores.get("local_utility", 0.0)
        cloud_val = scores.get("cloud_utility", 0.0)
        
        if local_val >= cloud_val:
            return RoutingDecision.LOCAL
        else:
            return RoutingDecision.CLOUD

    def calculate_confidence(self, constraint: ConstraintDecision, scores: dict) -> float:
        if constraint != ConstraintDecision.NONE:
            return 1.0
            
        local_val = scores.get("local_utility", 0.0)
        cloud_val = scores.get("cloud_utility", 0.0)
        
        diff = abs(local_val - cloud_val)
        max_val = max(local_val, cloud_val, 0.001)
        
        confidence = diff / max_val
        return min(max(confidence, 0.0), 1.0)
