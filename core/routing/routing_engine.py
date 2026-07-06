import time
import logging
from core.routing.routing_models import (
    RoutingContext,
    RoutingResult,
    RoutingDecision,
    ConstraintDecision,
    DecisionTrace
)
from core.routing.feature_extractor import FeatureExtractor
from core.routing.constraint_engine import ConstraintEngine
from core.routing.score_engine import ScoreEngine
from core.routing.decision_engine import DecisionEngine
from core.routing.explainability import ExplainabilityEngine
from core.routing.routing_logger import RoutingLogger

log = logging.getLogger("helios.routing.engine")

class RoutingEngine:
    def __init__(self):
        self.extractor = FeatureExtractor()
        self.constraints = ConstraintEngine()
        self.scores = ScoreEngine()
        self.decisions = DecisionEngine()
        self.explainers = ExplainabilityEngine()
        self.logger = RoutingLogger()
        log.info("Research RoutingEngine foundation initialized successfully.")

    def route(self, context: RoutingContext) -> RoutingResult:
        start_time = time.perf_counter()
        log.info("RoutingEngine.route called for prompt='%s'", context.prompt)
        
        # 1. Feature Extraction
        features = self.extractor.extract(context)
        
        # 2. Constraints Check (Stops early if a constraint forces a route)
        constraint, triggered_constraints = self.constraints.evaluate(context, features)
        
        # 3. Model-Aware Utility Scoring (evaluating specific candidate profiles)
        local_model = context.active_local_model or "gemma3"
        cloud_model = context.active_cloud_model or "gemini-2.0-flash"
        
        local_eval = self.scores.evaluate_model_utility(local_model, context, features)
        cloud_eval = self.scores.evaluate_model_utility(cloud_model, context, features)
        
        local_utility = local_eval["total_utility"]
        cloud_utility = cloud_eval["total_utility"]
        
        utility_scores = {
            "local_utility": local_utility,
            "cloud_utility": cloud_utility
        }
        
        # 4. Decision Logic (Chooses higher score or constraint override)
        decision = self.decisions.make_decision(context, features, constraint, utility_scores)
        
        # 5. Confidence Score (Normalized relative difference)
        confidence = self.decisions.calculate_confidence(constraint, utility_scores)
        
        # 6. Determine Selected Model
        selected_model = ""
        if decision == RoutingDecision.LOCAL:
            selected_model = local_model
        elif decision == RoutingDecision.CLOUD:
            selected_model = cloud_model
        else:
            selected_model = "None"
            
        # 7. Generate Explainability
        explanation = self.explainers.explain(
            decision, features, constraint, triggered_constraints, selected_model, confidence=confidence
        )
        
        execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        
        # 8. Create DecisionTrace
        trace = DecisionTrace(
            extracted_features={
                "privacy_score": features.privacy_score,
                "freshness_score": features.freshness_score,
                "complexity_score": features.complexity_score,
                "requires_internet": features.requires_internet,
                "contains_local_data": features.contains_local_data,
                "contains_sensitive_data": features.contains_sensitive_data
            },
            triggered_constraints=triggered_constraints,
            local_score=local_utility,
            cloud_score=cloud_utility,
            routing_decision=decision.value,
            confidence=confidence,
            score_breakdown={
                "local_breakdown": local_eval["breakdown"],
                "cloud_breakdown": cloud_eval["breakdown"]
            }
        )
        
        # 9. Assemble Result
        result = RoutingResult(
            decision=decision,
            features=features,
            context=context,
            scores=utility_scores,
            explanation=explanation,
            execution_time_ms=execution_time_ms,
            selected_model=selected_model,
            constraints_triggered=triggered_constraints,
            algorithm_name="CAHRA",
            algorithm_version="CAHRA-v1.0",
            strategy_name="Capability-Aware Weighted Hybrid Routing",
            decision_trace=trace
        )
        
        # 10. Log structured result
        try:
            self.logger.log_route(result)
        except Exception as log_exc:
            log.error("Failed to log route trace: %s", log_exc)
            
        return result
