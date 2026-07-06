import time
import logging
from core.routing.routing_models import (
    RoutingContext,
    RoutingResult,
    RoutingDecision
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
        
        # 2. Constraints Check
        constraint, triggered_constraints = self.constraints.evaluate(context, features)
        
        # 3. Scoring Evaluation (Placeholder utilities)
        utility_scores = self.scores.evaluate_scores(context, features)
        
        # 4. Decision Logic
        decision = self.decisions.make_decision(context, features, constraint, utility_scores)
        
        # 5. Determine Selected Model based on decision
        selected_model = ""
        if decision == RoutingDecision.LOCAL:
            selected_model = context.active_local_model or "gemma3"
        elif decision == RoutingDecision.CLOUD:
            selected_model = context.active_cloud_model or "gemini-2.0-flash"
        else:
            selected_model = "None"
            
        # 6. Generate Explainability
        explanation = self.explainers.explain(
            decision, features, constraint, triggered_constraints, selected_model
        )
        
        execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        
        # 7. Assemble Result
        result = RoutingResult(
            decision=decision,
            features=features,
            context=context,
            scores=utility_scores,
            explanation=explanation,
            execution_time_ms=execution_time_ms,
            selected_model=selected_model,
            constraints_triggered=triggered_constraints
        )
        
        # 8. Log structured result
        try:
            self.logger.log_route(result)
        except Exception as log_exc:
            log.error("Failed to log route trace: %s", log_exc)
            
        return result
