"""
HELIOS v2 - Dependency Optimizer
Prunes redundant transitive dependencies in the execution plan.
"""
from typing import List, Set
from core.reasoning.reasoning_models import AtomicTask

class DependencyOptimizer:
    def optimize(self, tasks: List[AtomicTask]) -> List[AtomicTask]:
        task_map = {t.task_id: t for t in tasks}
        
        def has_path(src_id: str, dest_id: str, visited: Set[str]) -> bool:
            if src_id == dest_id:
                return True
            src_task = task_map.get(src_id)
            if not src_task:
                return False
            for dep in src_task.dependencies:
                if dep not in visited:
                    if has_path(dep, dest_id, visited | {dep}):
                        return True
            return False

        refined_tasks = []
        for t in tasks:
            optimized_deps = []
            for dep in t.dependencies:
                # Check if there is an alternative path from t to dep through other direct dependencies
                is_redundant = False
                for other_dep in t.dependencies:
                    if other_dep != dep:
                        if has_path(other_dep, dep, {other_dep}):
                            is_redundant = True
                            break
                            
                if not is_redundant:
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
