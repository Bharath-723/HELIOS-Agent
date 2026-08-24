"""
HELIOS v2 - Plan Optimizer Loop
Executes iterative refinement passes until convergence, handles loop detection via fingerprints, and rolls back non-improving changes.
"""
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from core.reasoning.reasoning_models import (
    ExecutionGraph,
    PlanOptimizationTrace,
    OptimizationHistoryNode,
    TaskIntent,
    ReasoningContext
)
from core.reasoning.plan_analyzer import PlanAnalyzer
from core.reasoning.plan_refiner import PlanRefiner
from core.reasoning.strategy_evaluator import StrategyEvaluator
from core.reasoning.optimization_metrics import OptimizationMetricsCalculator

log = logging.getLogger("helios.reasoning.optimizer")

class PlanOptimizer:
    def __init__(self, rules_path: Optional[str] = None):
        if rules_path is None:
            rules_path = str(Path(__file__).parent / "optimization_rules.json")
        self.rules = self._load_rules(rules_path)
        
        self.analyzer = PlanAnalyzer()
        self.refiner = PlanRefiner()
        self.evaluator = StrategyEvaluator()
        self.metrics_calc = OptimizationMetricsCalculator()

    def _load_rules(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            log.error("Failed to load optimization rules: %s", exc)
            return {}

    def _get_fingerprint(self, graph: ExecutionGraph) -> str:
        # Deterministic representation of task order, models, and tools
        repr_str = "|".join(
            f"{t.task_id}:{t.required_model}:{t.required_tool}:{sorted(t.dependencies)}" 
            for t in sorted(graph.tasks.values(), key=lambda x: x.task_id)
        )
        return hashlib.sha256(repr_str.encode("utf-8")).hexdigest()[:16]

    def optimize_plan(
        self, intent: TaskIntent, context: ReasoningContext, graph: ExecutionGraph
    ) -> Tuple[ExecutionGraph, PlanOptimizationTrace]:
        log.info("Starting Cognitive Plan Optimization loop...")
        
        # Load rule parameters
        loop_settings = self.rules.get("loop_settings", {})
        max_iters = loop_settings.get("max_iterations", 5)
        conv_thresh = loop_settings.get("convergence_threshold", 0.005)

        # Baseline evaluation
        current_graph = graph
        current_eval = self.evaluator.evaluate(intent, current_graph)
        current_fingerprint = self._get_fingerprint(current_graph)

        original_graph = graph
        original_eval = current_eval
        original_fingerprint = current_fingerprint

        history: List[OptimizationHistoryNode] = []
        seen_fingerprints = {current_fingerprint}

        history.append(
            OptimizationHistoryNode(
                iteration=0,
                fingerprint=current_fingerprint,
                graph=current_graph,
                utility=current_eval.utility_score,
                decision_taken="Baseline plan generated."
            )
        )

        opt_confidence = 1.0

        for i in range(1, max_iters + 1):
            log.info("Optimization Iteration %d...", i)
            
            # 1. Analyze
            findings = self.analyzer.analyze(current_graph)
            
            # 2. Refine
            refined_graph, message = self.refiner.refine(current_graph)
            refined_fingerprint = self._get_fingerprint(refined_graph)

            # Loop detection
            if refined_fingerprint in seen_fingerprints:
                log.info("Optimization converged: loop/duplicate fingerprint detected. Stopping.")
                history.append(
                    OptimizationHistoryNode(
                        iteration=i,
                        fingerprint=refined_fingerprint,
                        graph=current_graph,
                        utility=current_eval.utility_score,
                        decision_taken="Loop detected. Convergence achieved."
                    )
                )
                break

            # 3. Evaluate
            refined_eval = self.evaluator.evaluate(intent, refined_graph)
            diff = refined_eval.utility_score - current_eval.utility_score

            log.info("Iteration %d Utility check: current=%.4f, refined=%.4f (diff=%.4f)", 
                     i, current_eval.utility_score, refined_eval.utility_score, diff)

            # 4. Rollback and Convergence logic
            if diff < 0.0:
                log.info("Rollback triggered: refined utility (%.4f) is worse than current (%.4f). Restoring previous state.", 
                         refined_eval.utility_score, current_eval.utility_score)
                history.append(
                    OptimizationHistoryNode(
                        iteration=i,
                        fingerprint=refined_fingerprint,
                        graph=refined_graph,
                        utility=refined_eval.utility_score,
                        decision_taken="Rollback applied (Utility decreased)."
                    )
                )
                opt_confidence *= 0.8
                break
                
            elif diff < conv_thresh:
                log.info("Optimization converged: utility gain (%.4f) is below threshold (%.4f). Stopping.", 
                         diff, conv_thresh)
                # Still commit this change as it's non-negative, but stop iterating
                current_graph = refined_graph
                current_eval = refined_eval
                current_fingerprint = refined_fingerprint
                seen_fingerprints.add(current_fingerprint)
                history.append(
                    OptimizationHistoryNode(
                        iteration=i,
                        fingerprint=current_fingerprint,
                        graph=current_graph,
                        utility=current_eval.utility_score,
                        decision_taken=f"Converged below threshold. Applied: {message}"
                    )
                )
                break
                
            else:
                # Committing improvement
                current_graph = refined_graph
                current_eval = refined_eval
                current_fingerprint = refined_fingerprint
                seen_fingerprints.add(current_fingerprint)
                history.append(
                    OptimizationHistoryNode(
                        iteration=i,
                        fingerprint=current_fingerprint,
                        graph=current_graph,
                        utility=current_eval.utility_score,
                        decision_taken=f"Transformation applied: {message}"
                    )
                )

        # Calculate final optimization metrics
        final_metrics = self.metrics_calc.calculate_gains(
            original_eval, current_eval, original_graph, current_graph
        )

        trace = PlanOptimizationTrace(
            original_fingerprint=original_fingerprint,
            final_fingerprint=current_fingerprint,
            original_utility=original_eval.utility_score,
            final_utility=current_eval.utility_score,
            history=history,
            optimization_confidence=round(opt_confidence, 4),
            metrics=final_metrics
        )

        log.info("Cognitive Plan Optimization completed. Utility gain: %.4f", final_metrics.utility_improvement)
        return current_graph, trace
