"""
HELIOS v2 - Strategy Evaluator
Computes performance metrics, utility scores, and utility breakdowns using configurable weights.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.reasoning.reasoning_models import (
    AtomicTask,
    ExecutionGraph,
    StrategyEvaluation,
    TaskIntent
)
from core.reasoning.planning_heuristics import PlanningHeuristicsEngine

log = logging.getLogger("helios.reasoning.evaluator")

class StrategyEvaluator:
    def __init__(self, weights_path: Optional[str] = None):
        if weights_path is None:
            weights_path = str(Path(__file__).parent / "planning_weights.json")
        self.weights = self._load_weights(weights_path)
        self.heuristics_engine = PlanningHeuristicsEngine()

    def _load_weights(self, path: str) -> Dict[str, float]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k: float(v) for k, v in data.get("weights", {}).items()}
        except Exception as exc:
            log.error("Failed to load utility weights: %s", exc)
            return {}

    def evaluate(self, intent: TaskIntent, graph: ExecutionGraph) -> StrategyEvaluation:
        tasks = list(graph.tasks.values())
        
        # 1. Base metric computations
        total_cost = sum(t.estimated_cost for t in tasks)
        max_risk = max(t.estimated_risk for t in tasks) if tasks else 0.0
        
        # Latency is sequential sum of parallel level max latencies
        level_latencies = []
        for group in graph.parallel_groups:
            if group:
                max_level_latency = max(graph.tasks[tid].estimated_latency_ms for tid in group if tid in graph.tasks)
                level_latencies.append(max_level_latency)
        total_latency = sum(level_latencies)

        # Ratios & efficiency scores via heuristics engine
        privacy_score = self.heuristics_engine.evaluate_locality(tasks)
        tool_score = self.heuristics_engine.evaluate_tool_utilization(tasks)
        parallel_efficiency = self.heuristics_engine.evaluate_parallel_efficiency(tasks, graph.parallel_groups)
        
        complexity = intent.complexity_score
        failure_prob = max_risk
        
        # Standardize metrics to [0, 1] range for scoring
        # Lower cost is better
        norm_cost = 1.0 / (1.0 + total_cost * 100.0) 
        # Lower latency is better
        norm_latency = 1.0 / (1.0 + total_latency / 1000.0) 
        # Lower failure prob is better
        norm_fail = 1.0 - failure_prob 
        # Lower complexity is better
        norm_comp = 1.0 - complexity 

        # 2. Utility Score Computation
        utility_score = 0.0
        breakdown = {}
        
        metric_map = {
            "cost": norm_cost,
            "latency": norm_latency,
            "complexity": norm_comp,
            "parallel_efficiency": parallel_efficiency,
            "failure_probability": norm_fail,
            "privacy_score": privacy_score,
            "tool_utilization": tool_score,
            "maintainability": 0.8,         # Baseline
            "recovery_capability": 0.7      # Baseline
        }

        for metric_name, value in metric_map.items():
            w = self.weights.get(metric_name, 0.0)
            # Multiply by absolute or sign depending on weights configuration
            contrib = w * value
            utility_score += contrib
            breakdown[f"{metric_name}_contribution"] = round(contrib, 4)

        return StrategyEvaluation(
            cost=total_cost,
            latency=total_latency,
            complexity=complexity,
            parallel_efficiency=parallel_efficiency,
            failure_probability=failure_prob,
            privacy_score=privacy_score,
            tool_utilization=tool_score,
            utility_score=round(utility_score, 4),
            utility_breakdown=breakdown
        )
