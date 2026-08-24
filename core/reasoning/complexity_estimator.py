"""
HELIOS v2 - Planning Complexity Estimator
Calculates planning-level metrics including total latency, total cost, maximum risk, DAG depth, and parallelization factors.
"""
from typing import List, Dict, Any
from core.reasoning.reasoning_models import AtomicTask

class PlanningComplexityEstimator:
    def estimate(self, tasks: List[AtomicTask], parallel_groups: List[List[str]]) -> Dict[str, Any]:
        total_tasks = len(tasks)
        if total_tasks == 0:
            return {
                "total_estimated_latency_ms": 0.0,
                "total_estimated_cost": 0.0,
                "max_estimated_risk": 0.0,
                "graph_depth": 0,
                "parallel_factor": 0.0,
                "concurrency_index": 0.0
            }

        total_cost = sum(t.estimated_cost for t in tasks)
        max_risk = max(t.estimated_risk for t in tasks)
        
        # Latency estimation: tasks in a parallel group run concurrently,
        # so the latency of a level is the maximum latency among its members.
        level_latencies = []
        task_dict = {t.task_id: t for t in tasks}
        
        for group in parallel_groups:
            if group:
                max_level_latency = max(task_dict[tid].estimated_latency_ms for tid in group if tid in task_dict)
                level_latencies.append(max_level_latency)
                
        total_latency = sum(level_latencies)
        graph_depth = len(parallel_groups)
        
        # Parallelization Factor: avg tasks per level
        parallel_factor = total_tasks / max(1, graph_depth)
        
        # Concurrency Index: percentage of parallel levels containing >1 task
        parallel_levels_count = sum(1 for g in parallel_groups if len(g) > 1)
        concurrency_index = parallel_levels_count / max(1, graph_depth)

        return {
            "total_estimated_latency_ms": total_latency,
            "total_estimated_cost": total_cost,
            "max_estimated_risk": max_risk,
            "graph_depth": graph_depth,
            "parallel_factor": round(parallel_factor, 2),
            "concurrency_index": round(concurrency_index, 2)
        }
