"""
HELIOS v2 - Parallel Optimizer
Maximizes parallel execution blocks by ensuring independent tasks do not have artificial dependencies.
"""
from typing import List
from core.reasoning.reasoning_models import AtomicTask

class ParallelOptimizer:
    def optimize(self, tasks: List[AtomicTask]) -> List[AtomicTask]:
        task_map = {t.task_id: t for t in tasks}
        refined_tasks = []
        for t in tasks:
            optimized_deps = []
            for dep in t.dependencies:
                dep_task = task_map.get(dep)
                if dep_task:
                    # Prune network check dependency if this task is a local note/file operation
                    # that does not require network access.
                    if "connectivity" in dep_task.description.lower() or "check" in dep_task.description.lower():
                        if "note" in t.description.lower() or "file" in t.description.lower():
                            # Artificial dependency pruned
                            continue
                optimized_deps.append(dep)
                
            refined_task = AtomicTask(
                task_id=t.task_id,
                description=t.description,
                expected_output=t.expected_output,
                required_tool=t.required_tool,
                required_model=t.required_model,
                fallback_strategy=t.fallback_strategy,
                estimated_cost=t.estimated_cost,
                estimated_latency_ms=t.estimated_latency_ms,
                estimated_risk=t.estimated_risk,
                dependencies=optimized_deps,
                state=t.state,
                execution_result=t.execution_result,
                priority=t.priority,
                retry_limit=t.retry_limit,
                verification_required=t.verification_required,
                cacheable=t.cacheable,
                preconditions=t.preconditions.copy(),
                postconditions=t.postconditions.copy(),
                failure_mode=t.failure_mode,
                timeout=t.timeout,
                resource_requirements=t.resource_requirements.copy(),
                execution_constraints=t.execution_constraints.copy()
            )
            refined_tasks.append(refined_task)
            
        return refined_tasks
