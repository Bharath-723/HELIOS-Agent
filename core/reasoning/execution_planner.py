"""
HELIOS v2 - Execution Planner
Assigns models, tools, estimated latency, costs, and risks to each AtomicTask based on ReasoningContext constraints.
"""
from typing import List
from core.reasoning.reasoning_models import AtomicTask, ReasoningContext

class ExecutionPlanner:
    def optimize_plan(self, tasks: List[AtomicTask], context: ReasoningContext) -> List[AtomicTask]:
        optimized = []
        
        for task in tasks:
            # Copy metrics to adjust based on context
            model = task.required_model
            latency = task.estimated_latency_ms
            risk = task.estimated_risk
            cost = task.estimated_cost
            
            # Constraint 1: Internet offline fallback
            if not context.internet_available and task.required_tool in ("WebSearch", "GmailComposer"):
                # Force local fallback
                model = "gemma3"
                cost = 0.0
                latency *= 0.5 # offline error/fallback resolves immediately
                risk = 0.9     # extremely high risk since internet is offline
                
            # Constraint 2: Local model offline fallback
            if not context.local_model_available and model in ("gemma3", "mistral"):
                # Force cloud fallback
                model = "gemini-2.0-flash"
                cost += 0.002
                latency += 1000.0  # Network overhead
                risk = 0.2
                
            # Constraint 3: Low RAM overhead adjustments
            if context.hardware_specs.get("low_ram_mode", False) and model in ("gemma3", "mistral"):
                # Increase latency and risk due to swapping / local resource constraints
                latency *= 1.30
                risk *= 1.20
                
            optimized_task = AtomicTask(
                task_id=task.task_id,
                description=task.description,
                expected_output=task.expected_output,
                required_tool=task.required_tool,
                required_model=model,
                fallback_strategy=task.fallback_strategy,
                estimated_cost=cost,
                estimated_latency_ms=latency,
                estimated_risk=risk,
                dependencies=task.dependencies.copy(),
                state=task.state,
                execution_result=task.execution_result
            )
            optimized.append(optimized_task)
            
        return optimized
