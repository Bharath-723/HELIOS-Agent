"""
HELIOS v2 - Central Reasoning Engine
Coordinates cognitive planning components and outputs explained, validated, optimized adaptive ExecutionPlans.
"""
import uuid
import time
import logging
from typing import Optional, List
from core.reasoning.reasoning_models import (
    ReasoningContext,
    ExecutionPlan,
    ValidationResult,
    AtomicTask
)
from core.reasoning.intent_understanding import IntentUnderstandingEngine
from core.reasoning.task_understanding import TaskUnderstandingEngine
from core.reasoning.task_planner import TaskPlanner
from core.reasoning.complexity_estimator import PlanningComplexityEstimator
from core.reasoning.adaptive_planner import AdaptivePlanner
from core.reasoning.plan_optimizer import PlanOptimizer
from core.reasoning.plan_explanation import PlanExplanationEngine
from core.reasoning.planning_validator import PlanningValidator
from core.reasoning.planning_logger import PlanningLogger

log = logging.getLogger("helios.reasoning.engine")

class ReasoningEngine:
    def __init__(self, rules_path: Optional[str] = None):
        self.intent_engine = IntentUnderstandingEngine(rules_path)
        self.task_understanding_engine = TaskUnderstandingEngine()
        self.task_planner = TaskPlanner()
        self.complexity_estimator = PlanningComplexityEstimator()
        self.adaptive_planner = AdaptivePlanner()
        self.plan_optimizer = PlanOptimizer()
        self.explainability_engine = PlanExplanationEngine()
        self.validator = PlanningValidator()
        self.planner_logger = PlanningLogger()
        log.info("Cognitive Reasoning Engine initialized successfully.")

    def plan(self, prompt: str, context: ReasoningContext) -> ExecutionPlan:
        t0 = time.perf_counter()
        
        # 1. Parse intent
        intent = self.intent_engine.parse(prompt)
        
        # 2. Derive task understanding
        understanding = self.task_understanding_engine.analyze(intent)
        
        # 3. Decompose subtasks (baseline list)
        subtasks = self.task_planner.plan_subtasks(intent)
        
        # 4. Complexity Estimation (Moved BEFORE Strategy Generation to influence candidate creation)
        baseline_parallel_groups = [[t.task_id] for t in subtasks]
        complexity_metrics = self.complexity_estimator.estimate(subtasks, baseline_parallel_groups)
        
        # 5. Strategy Generation, Constraint Filtering, Evaluation, Ranking, and Selection
        graph, trace, selection = self.adaptive_planner.plan_adaptive(intent, context, complexity_metrics)
        
        # 6. Autonomous Plan Refinement & Optimization Loop (New Sprint 3 additions)
        optimized_graph, opt_trace = self.plan_optimizer.optimize_plan(intent, context, graph)
        
        # 7. Extract final tasks list from optimized graph
        final_tasks = list(optimized_graph.tasks.values())
        
        # 8. Generate explanation object for the optimized graph
        explanation = self.explainability_engine.explain(intent, understanding, final_tasks)
        
        # 9. Validate execution plan
        validation_result = self.validator.validate(intent, context, final_tasks)
        
        # 10. Measure planning parameters
        planning_time_ms = (time.perf_counter() - t0) * 1000.0
        
        # Determine planning confidence based on context availability and task complexity
        confidence = 1.0 - (intent.complexity_score * 0.4)
        if intent.requires_internet and not context.internet_available:
            confidence *= 0.5
        if len(intent.requires_tools) > 0 and not any(t in context.available_tools for t in intent.requires_tools):
            confidence *= 0.2
            
        decision_path = (
            f"Parsed prompt intent category '{intent.category.value}' with complexity {intent.complexity_score:.2f}. "
            f"Selected strategy: '{selection.selected_strategy_name}'. "
            f"Optimization gain: {opt_trace.metrics.utility_improvement:.4f} (latency reduction: {opt_trace.metrics.latency_reduction_ms:.1f}ms). "
            f"Validation status: {validation_result.status}."
        )
        
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4())[:8],
            prompt=prompt,
            intent=intent,
            understanding=understanding,
            context=context,
            graph=optimized_graph,
            explanation=explanation,
            complexity_metrics=complexity_metrics,
            validation_result=validation_result,
            trace=trace,
            selection=selection,
            optimization_trace=opt_trace,
            planning_time_ms=planning_time_ms,
            planning_confidence=confidence,
            decision_path_summary=decision_path
        )
        
        # Log plan trace
        self.planner_logger.log_plan(plan)
        
        return plan
