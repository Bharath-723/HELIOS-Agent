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
from core.routing.candidate_manager import CandidateManager

log = logging.getLogger("helios.routing.engine")

class RoutingEngine:
    def __init__(self):
        self.extractor = FeatureExtractor()
        self.constraints = ConstraintEngine()
        self.scores = ScoreEngine()
        self.decisions = DecisionEngine()
        self.explainers = ExplainabilityEngine()
        self.logger = RoutingLogger()
        self.candidate_mgr = CandidateManager()
        log.info("Research RoutingEngine (Ranker) initialized successfully.")

    def route(self, context: RoutingContext) -> RoutingResult:
        start_time = time.perf_counter()
        log.info("RoutingEngine.route called for prompt='%s'", context.prompt)
        
        # 1. Feature Extraction
        features = self.extractor.extract(context)
        
        # 2. Constraints Check
        constraint, triggered_constraints = self.constraints.evaluate(context, features)
        
        # 3. Retrieve available candidate models
        available_models = self.candidate_mgr.get_available_candidates(context)
        if not available_models:
            available_models = ["gemma3"]
            
        # 4. Evaluate each candidate model
        model_utilities = {}
        model_breakdowns = {}
        mismatches = {}
        
        r_p = features.privacy_score
        r_f = features.freshness_score
        r_cx = features.complexity_score
        
        for model in available_models:
            eval_res = self.scores.evaluate_model_utility(model, context, features)
            model_utilities[model] = eval_res["total_utility"]
            model_breakdowns[model] = eval_res["breakdown"]
            
            eff = self.scores.get_effective_capability(model, context)
            mismatches[model] = {
                "privacy": abs(r_p - eff["privacy"]),
                "freshness": abs(r_f - eff["freshness"]),
                "complexity": abs(r_cx - eff["complexity"])
            }
            
        # 5. Rank Candidates by total utility (descending)
        ranked_candidates = sorted(available_models, key=lambda m: model_utilities[m], reverse=True)
        best_candidate = ranked_candidates[0]
        
        # 6. Compute Selection Margin
        highest_utility = model_utilities[best_candidate]
        if len(ranked_candidates) > 1:
            second_candidate = ranked_candidates[1]
            second_utility = model_utilities[second_candidate]
            selection_margin = highest_utility - second_utility
        else:
            selection_margin = highest_utility
            
        # 7. Resolve final routing decision
        forced_candidate = None
        if constraint == ConstraintDecision.FORCE_LOCAL:
            local_cands = [m for m in ranked_candidates if self.candidate_mgr.profiles.get(m, {}).get("type") == "local"]
            if local_cands:
                forced_candidate = local_cands[0]
                decision = RoutingDecision.LOCAL
            else:
                decision = RoutingDecision.LOCAL
        elif constraint == ConstraintDecision.FORCE_CLOUD:
            cloud_cands = [m for m in ranked_candidates if self.candidate_mgr.profiles.get(m, {}).get("type") == "cloud"]
            if cloud_cands:
                forced_candidate = cloud_cands[0]
                decision = RoutingDecision.CLOUD
            else:
                decision = RoutingDecision.CLOUD
        else:
            best_type = self.candidate_mgr.profiles.get(best_candidate, {}).get("type", "local")
            decision = RoutingDecision.LOCAL if best_type == "local" else RoutingDecision.CLOUD
            
        selected_model = forced_candidate if forced_candidate else best_candidate
        
        # 8. Compute Confidence
        if constraint != ConstraintDecision.NONE:
            confidence = 1.0
        else:
            confidence = selection_margin / max(highest_utility, 0.001)
            confidence = min(max(confidence, 0.0), 1.0)
            
        # 9. Generate Explainability
        explanation = self.explainers.explain(
            decision, features, constraint, triggered_constraints, selected_model,
            confidence=confidence,
            candidate_ranking=ranked_candidates,
            capability_mismatches=mismatches,
            selection_margin=selection_margin
        )
        
        execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        
        # 10. Assemble trace
        local_model_name = context.active_local_model or "gemma3"
        cloud_model_name = context.active_cloud_model or "gemini-2.0-flash"
        
        trace = DecisionTrace(
            extracted_features={
                "privacy_score": r_p,
                "freshness_score": r_f,
                "complexity_score": r_cx,
                "requires_internet": features.requires_internet,
                "contains_local_data": features.contains_local_data,
                "contains_sensitive_data": features.contains_sensitive_data
            },
            triggered_constraints=triggered_constraints,
            local_score=model_utilities.get(local_model_name, 0.5),
            cloud_score=model_utilities.get(cloud_model_name, 0.5),
            routing_decision=decision.value,
            confidence=confidence,
            score_breakdown={
                "local_breakdown": model_breakdowns.get(local_model_name, {}),
                "cloud_breakdown": model_breakdowns.get(cloud_model_name, {}),
                "all_candidates_utilities": model_utilities
            }
        )
        
        result = RoutingResult(
            decision=decision,
            features=features,
            context=context,
            scores={
                "local_utility": model_utilities.get(local_model_name, 0.5),
                "cloud_utility": model_utilities.get(cloud_model_name, 0.5)
            },
            explanation=explanation,
            execution_time_ms=execution_time_ms,
            selected_model=selected_model,
            constraints_triggered=triggered_constraints,
            algorithm_name="CAHRA",
            algorithm_version="CAHRA-v1.0",
            strategy_name="Capability-Aware Weighted Hybrid Routing",
            decision_trace=trace,
            candidate_ranking=ranked_candidates,
            best_candidate=best_candidate,
            selection_margin=selection_margin,
            capability_mismatches=mismatches
        )
        
        try:
            self.logger.log_route(result)
        except Exception as log_exc:
            log.error("Failed to log route trace: %s", log_exc)
            
        return result
