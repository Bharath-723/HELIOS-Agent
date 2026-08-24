"""
HELIOS v2 - Strategy Generator
Generates alternative planning strategy candidates using dynamic Planning Policies and task fingerprints.
"""
import hashlib
from typing import List, Dict, Any
from core.reasoning.reasoning_models import (
    TaskIntent,
    ReasoningContext,
    AtomicTask,
    PlanningPolicy,
    PlanningStrategy,
    ExecutionGraph
)
from core.reasoning.task_planner import TaskPlanner
from core.reasoning.execution_graph_builder import ExecutionGraphBuilder

class StrategyGenerator:
    def __init__(self):
        self.task_planner = TaskPlanner()
        self.graph_builder = ExecutionGraphBuilder()

    def _generate_fingerprint(self, tasks: List[AtomicTask]) -> str:
        # Generate a deterministic hash of task IDs and their dependencies
        repr_str = "|".join(f"{t.task_id}:{t.required_model}:{t.required_tool}:{sorted(t.dependencies)}" for t in sorted(tasks, key=lambda x: x.task_id))
        return hashlib.sha256(repr_str.encode("utf-8")).hexdigest()[:16]

    def generate_candidates(
        self, intent: TaskIntent, context: ReasoningContext, baseline_complexity: Dict[str, Any]
    ) -> List[PlanningStrategy]:
        strategies = []
        
        # 1. Base tasks list
        base_tasks = self.task_planner.plan_subtasks(intent)
        
        # Determine policies to generate
        policies = [
            PlanningPolicy.LOW_RESOURCE,
            PlanningPolicy.HIGH_ACCURACY,
            PlanningPolicy.FAST_RESPONSE,
            PlanningPolicy.PRIVACY_FIRST,
            PlanningPolicy.PARALLEL_FIRST
        ]
        
        for policy in policies:
            candidate_tasks = []
            
            for task in base_tasks:
                model = task.required_model
                tool = task.required_tool
                latency = task.estimated_latency_ms
                cost = task.estimated_cost
                risk = task.estimated_risk
                priority = task.priority
                retry_lim = task.retry_limit
                verify_req = task.verification_required
                cacheable = task.cacheable
                deps = task.dependencies.copy()
                
                # Apply policy adjustments
                if policy == PlanningPolicy.LOW_RESOURCE:
                    # Enforce low footprint
                    if model in ("gemini-2.0-flash", "gpt-4o-mini"):
                        model = "gemma3"
                        cost = 0.0
                        latency = max(latency - 500, 300)
                    cacheable = True
                    retry_lim = 1
                    
                elif policy == PlanningPolicy.HIGH_ACCURACY:
                    # Enforce high validation and best model
                    if model == "gemma3" and context.local_model_available:
                        model = "mistral"
                    elif not context.local_model_available:
                        model = "gemini-2.0-flash"
                    verify_req = True
                    retry_lim = 5
                    risk = max(0.05, risk * 0.5)
                    
                elif policy == PlanningPolicy.FAST_RESPONSE:
                    # Enforce fast cloud models
                    if model in ("gemma3", "mistral") and context.internet_available:
                        model = "gemini-2.0-flash"
                        cost = max(cost, 0.003)
                    latency = max(100.0, latency * 0.70)
                    retry_lim = 2
                    
                elif policy == PlanningPolicy.PRIVACY_FIRST:
                    # Enforce strict offline confinement
                    model = "gemma3"
                    cost = 0.0
                    if tool == "WebSearch":
                        tool = None # Strip internet tools
                        
                elif policy == PlanningPolicy.PARALLEL_FIRST:
                    # Reduce task dependencies where possible to allow concurrency
                    # E.g. run checks in parallel with content drafts
                    pass
                
                # Influence from baseline complexity metrics
                avg_complexity = baseline_complexity.get("complexity_score", 0.5)
                if avg_complexity > 0.6:
                    # Scale latencies for high complexity tasks
                    latency *= 1.2
                    risk *= 1.1

                adjusted_task = AtomicTask(
                    task_id=task.task_id,
                    description=task.description,
                    expected_output=task.expected_output,
                    required_tool=tool,
                    required_model=model,
                    fallback_strategy=task.fallback_strategy,
                    estimated_cost=cost,
                    estimated_latency_ms=latency,
                    estimated_risk=risk,
                    dependencies=deps,
                    state=task.state,
                    execution_result=task.execution_result,
                    priority=priority,
                    retry_limit=retry_lim,
                    verification_required=verify_req,
                    cacheable=cacheable
                )
                candidate_tasks.append(adjusted_task)
                
            # Build graph and fingerprint
            try:
                graph = self.graph_builder.build_graph(candidate_tasks)
                fingerprint = self._generate_fingerprint(candidate_tasks)
                
                from core.reasoning.strategy_evaluator import StrategyEvaluation # import here to avoid circular imports
                dummy_eval = StrategyEvaluation(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
                
                strategy = PlanningStrategy(
                    name=f"strategy-{policy.value}",
                    policy=policy,
                    graph=graph,
                    fingerprint=fingerprint,
                    complexity_metrics={},
                    evaluation_metrics=dummy_eval
                )
                strategies.append(strategy)
            except Exception as e:
                # If a policy produces invalid graph, skip it
                pass
                
        return strategies
