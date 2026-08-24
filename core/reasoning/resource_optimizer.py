"""
HELIOS v2 - Resource Optimizer
Optimizes model assignments, tool reuse cycles, and cache parameters to minimize execution footprints.
"""
from typing import List
from core.reasoning.reasoning_models import AtomicTask

class ResourceOptimizer:
    def optimize(self, tasks: List[AtomicTask]) -> List[AtomicTask]:
        # Rule 1: Model Substitution
        # If the plan uses multiple different local models (e.g. gemma3 for task 1, mistral for task 2),
        # this incurs a double model load penalty. Substituting the weaker model for the stronger model
        # or standardizing on a single local model prevents resource thrashing.
        
        local_models_used = {t.required_model for t in tasks if t.required_model in ("gemma3", "mistral")}
        
        target_model = "gemma3"
        if "mistral" in local_models_used:
            # Standardize on mistral if it's already loaded/required for at least one task
            target_model = "mistral"
            
        refined_tasks = []
        for t in tasks:
            model = t.required_model
            # Substitute model if it avoids local loading mix
            if model in ("gemma3", "mistral") and len(local_models_used) > 1:
                model = target_model

            # Rule 2: Enforce cacheable options for read-only actions
            cacheable = t.cacheable
            if t.required_tool in ("WebSearch", "NotesManager") and "read" in t.description.lower():
                cacheable = True

            refined_task = AtomicTask(
                task_id=t.task_id,
                description=t.description,
                expected_output=t.expected_output,
                required_tool=t.required_tool,
                required_model=model,
                fallback_strategy=t.fallback_strategy,
                estimated_cost=t.estimated_cost,
                estimated_latency_ms=t.estimated_latency_ms,
                estimated_risk=t.estimated_risk,
                dependencies=t.dependencies.copy(),
                state=t.state,
                execution_result=t.execution_result,
                priority=t.priority,
                retry_limit=t.retry_limit,
                verification_required=t.verification_required,
                cacheable=cacheable,
                preconditions=t.preconditions.copy(),
                postconditions=t.postconditions.copy(),
                failure_mode=t.failure_mode,
                timeout=t.timeout,
                resource_requirements=t.resource_requirements.copy(),
                execution_constraints=t.execution_constraints.copy()
            )
            refined_tasks.append(refined_task)
            
        return refined_tasks
