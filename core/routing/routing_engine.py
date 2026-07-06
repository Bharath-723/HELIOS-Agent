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
        total_start = time.perf_counter()
        
        # 1. Feature Extraction Time
        t0 = time.perf_counter()
        features = self.extractor.extract(context)
        feat_time = (time.perf_counter() - t0) * 1000.0
        
        # 2. Constraints Check Time
        t1 = time.perf_counter()
        constraint, triggered_constraints = self.constraints.evaluate(context, features)
        constraint_time = (time.perf_counter() - t1) * 1000.0
        
        # 3. Score Calculation and Candidate Evaluation Time
        t2 = time.perf_counter()
        available_models = self.candidate_mgr.get_available_candidates(context)
        if not available_models:
            available_models = ["gemma3"]
            
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
        score_time = (time.perf_counter() - t2) * 1000.0
            
        # 4. Candidate Ranking and Decision Selection Time
        t3 = time.perf_counter()
        ranked_candidates = sorted(available_models, key=lambda m: model_utilities[m], reverse=True)
        best_candidate = ranked_candidates[0]
        
        highest_utility = model_utilities[best_candidate]
        if len(ranked_candidates) > 1:
            second_candidate = ranked_candidates[1]
            second_utility = model_utilities[second_candidate]
            selection_margin = highest_utility - second_utility
        else:
            selection_margin = highest_utility
            
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
        
        if constraint != ConstraintDecision.NONE:
            confidence = 1.0
        else:
            confidence = selection_margin / max(highest_utility, 0.001)
            confidence = min(max(confidence, 0.0), 1.0)
        ranking_time = (time.perf_counter() - t3) * 1000.0
            
        # 5. Explanation Generation Time
        t4 = time.perf_counter()
        explanation = self.explainers.explain(
            decision, features, constraint, triggered_constraints, selected_model,
            confidence=confidence,
            candidate_ranking=ranked_candidates,
            capability_mismatches=mismatches,
            selection_margin=selection_margin
        )
        explanation_time = (time.perf_counter() - t4) * 1000.0
        
        total_time_ms = (time.perf_counter() - total_start) * 1000.0
        
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
            execution_time_ms=total_time_ms,
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
        
        timings = {
            "feature_extraction_time_ms": feat_time,
            "constraint_evaluation_time_ms": constraint_time,
            "score_calculation_time_ms": score_time,
            "ranking_time_ms": ranking_time,
            "explanation_generation_time_ms": explanation_time,
            "total_time_ms": total_time_ms
        }
        
        try:
            from core.routing.routing_diagnostics import RoutingDiagnostics
            diagnostics = RoutingDiagnostics()
            snapshot = diagnostics.compile_snapshot(result, timings)
            result.decision_snapshot = snapshot
            
            log.info("CAHRA Timings Detail: Features=%.2fms, Constraints=%.2fms, Scores=%.2fms, Ranking=%.2fms, Explain=%.2fms, Total=%.2fms",
                     feat_time, constraint_time, score_time, ranking_time, explanation_time, total_time_ms)
        except Exception as snap_exc:
            log.error("Failed to compile decision snapshot in routing engine: %s", snap_exc)
            
        try:
            self.logger.log_route(result)
        except Exception as log_exc:
            log.error("Failed to log route trace: %s", log_exc)
            
        return result
