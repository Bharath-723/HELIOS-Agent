"""
HELIOS v2 - Optimization Metrics Calculator
Computes difference matrices between baseline plans and refined plan candidates.
"""
from typing import Dict, Any
from core.reasoning.reasoning_models import StrategyEvaluation, PlanOptimizationMetrics, ExecutionGraph

class OptimizationMetricsCalculator:
    def calculate_gains(
        self, 
        base_eval: StrategyEvaluation, 
        opt_eval: StrategyEvaluation,
        base_graph: ExecutionGraph,
        opt_graph: ExecutionGraph
    ) -> PlanOptimizationMetrics:
        
        # 1. Cost savings
        cost_savings = round(base_eval.cost - opt_eval.cost, 4)
        
        # 2. Latency reduction
        latency_red = round(base_eval.latency - opt_eval.latency, 2)
        
        # 3. Complexity reduction
        complexity_red = round(base_eval.complexity - opt_eval.complexity, 3)
        
        # 4. Dependency reduction
        base_dep_count = sum(len(t.dependencies) for t in base_graph.tasks.values())
        opt_dep_count = sum(len(t.dependencies) for t in opt_graph.tasks.values())
        dep_reduction = base_dep_count - opt_dep_count
        
        # 5. Parallelism increase
        base_par = len(base_graph.tasks) / max(1, len(base_graph.parallel_groups))
        opt_par = len(opt_graph.tasks) / max(1, len(opt_graph.parallel_groups))
        par_increase = round(opt_par - base_par, 2)
        
        # 6. Utility improvement
        util_improvement = round(opt_eval.utility_score - base_eval.utility_score, 4)
        
        # Combined gain score (0.0 to 1.0 or higher based on improvements)
        gain = 0.0
        if util_improvement > 0:
            gain = util_improvement
            
        return PlanOptimizationMetrics(
            gain=gain,
            latency_reduction_ms=latency_red,
            complexity_reduction=complexity_red,
            dependency_reduction=dep_reduction,
            parallelism_increase=par_increase,
            cost_savings=cost_savings,
            utility_improvement=util_improvement
        )
