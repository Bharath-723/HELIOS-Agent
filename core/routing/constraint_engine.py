import logging
from typing import List, Tuple
from core.routing.routing_models import (
    RoutingContext,
    RoutingFeatures,
    ConstraintDecision
)

log = logging.getLogger("helios.routing.constraint_engine")

class ConstraintEngine:
    def check_connectivity(self, context: RoutingContext, features: RoutingFeatures) -> Tuple[ConstraintDecision, str]:
        if features.requires_internet and not context.internet_available:
            log.info("Constraint triggered: internet required but unavailable. Force LOCAL.")
            return ConstraintDecision.FORCE_LOCAL, "Internet required but unavailable."
        return ConstraintDecision.NONE, ""

    def check_local_model(self, context: RoutingContext, features: RoutingFeatures) -> Tuple[ConstraintDecision, str]:
        if not context.local_model_available:
            log.info("Constraint triggered: local model unavailable. Force CLOUD.")
            return ConstraintDecision.FORCE_CLOUD, "Local inference service is offline."
        return ConstraintDecision.NONE, ""

    def check_cloud_model(self, context: RoutingContext, features: RoutingFeatures) -> Tuple[ConstraintDecision, str]:
        if not context.cloud_available:
            log.info("Constraint triggered: cloud provider unavailable. Force LOCAL.")
            return ConstraintDecision.FORCE_LOCAL, "Cloud provider is offline or unconfigured."
        return ConstraintDecision.NONE, ""

    def check_privacy(self, context: RoutingContext, features: RoutingFeatures) -> Tuple[ConstraintDecision, str]:
        if features.contains_sensitive_data or features.privacy_score >= 0.90:
            log.info("Constraint triggered: privacy/sensitive data constraints. Force LOCAL.")
            return ConstraintDecision.FORCE_LOCAL, "Sensitive data or high privacy requirements."
        return ConstraintDecision.NONE, ""

    def check_freshness(self, context: RoutingContext, features: RoutingFeatures) -> Tuple[ConstraintDecision, str]:
        if features.freshness_score >= 0.80:
            log.info("Constraint triggered: freshness constraints. Force CLOUD.")
            return ConstraintDecision.FORCE_CLOUD, "Real-time or fresh information required."
        return ConstraintDecision.NONE, ""

    def evaluate(self, context: RoutingContext, features: RoutingFeatures) -> Tuple[ConstraintDecision, List[str]]:
        reasons = []
        triggered = []

        # Strict priority evaluation:
        # 1. Internet connectivity
        # 2. Local model availability
        # 3. Cloud provider availability
        # 4. Privacy constraints
        # 5. Freshness constraints
        checks = [
            (self.check_connectivity, "check_connectivity"),
            (self.check_local_model, "check_local_model"),
            (self.check_cloud_model, "check_cloud_model"),
            (self.check_privacy, "check_privacy"),
            (self.check_freshness, "check_freshness")
        ]

        for check_func, name in checks:
            decision, reason = check_func(context, features)
            if decision != ConstraintDecision.NONE:
                reasons.append(reason)
                triggered.append(name)
                return decision, triggered

        return ConstraintDecision.NONE, []
