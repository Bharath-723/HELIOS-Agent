"""
HELIOS v2 - Adaptive Planner Coordinator
Integrates planning policies, heuristics, constraints, evaluation, ranking, selector, memory cache, and traces.
"""
import time
import logging
from typing import List, Dict, Any, Tuple
from core.reasoning.reasoning_models import (
    TaskIntent,
    ReasoningContext,
    PlanningStrategy,
    SelectionDecision,
    PlanningTrace,
    ExecutionGraph
)
from core.reasoning.strategy_generator import StrategyGenerator
from core.reasoning.planning_constraints import PlanningConstraintEvaluator
from core.reasoning.strategy_evaluator import StrategyEvaluator
from core.reasoning.strategy_ranker import StrategyRanker
from core.reasoning.strategy_selector import StrategySelector
from core.reasoning.planning_trace import PlanningTraceRecorder
from core.reasoning.planning_memory import PlanningMemory

log = logging.getLogger("helios.reasoning.adaptive")

class AdaptivePlanner:
    def __init__(self):
        self.generator = StrategyGenerator()
        self.constraint_evaluator = PlanningConstraintEvaluator()
        self.evaluator = StrategyEvaluator()
        self.ranker = StrategyRanker()
        self.selector = StrategySelector()
        self.memory = PlanningMemory()

    def plan_adaptive(
        self, intent: TaskIntent, context: ReasoningContext, baseline_complexity: Dict[str, Any]
    ) -> Tuple[ExecutionGraph, PlanningTrace, SelectionDecision]:
        t0 = time.perf_counter()
        trace_recorder = PlanningTraceRecorder()
        
        # Stage 1: Check Planning Memory Cache
        cached_graph = self.memory.get(intent, context)
        trace_recorder.record_stage(
            "planning_memory_check",
            input_summary={"intent_category": intent.category.name},
            output_summary={"cache_hit": cached_graph is not None}
        )

        # Stage 2: Strategy Generation (or reuse cached structure)
        all_candidates = []
        if cached_graph:
            # Reconstruct strategy based on cached topology
            from core.reasoning.reasoning_models import PlanningPolicy, StrategyEvaluation
            # Create a mock evaluation
            mock_eval = StrategyEvaluation(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
            cached_strategy = PlanningStrategy(
                name="strategy-cached-memory",
                policy=PlanningPolicy.LOW_RESOURCE,
                graph=cached_graph,
                fingerprint="cached-fingerprint",
                complexity_metrics=baseline_complexity,
                evaluation_metrics=mock_eval
            )
            all_candidates = [cached_strategy]
        else:
            all_candidates = self.generator.generate_candidates(intent, context, baseline_complexity)

        trace_recorder.record_stage(
            "strategy_generation",
            input_summary={"baseline_complexity": baseline_complexity},
            output_summary={"candidates_generated": [s.name for s in all_candidates]}
        )

        # Stage 3: Constraint Filtering (Multi-level Constraint Classification)
        filtered_candidates = []
        for s in all_candidates:
            is_valid, status_map = self.constraint_evaluator.evaluate_constraints(intent, context, list(s.graph.tasks.values()))
            # Update candidate strategy with constraint status mapping
            s_updated = PlanningStrategy(
                name=s.name,
                policy=s.policy,
                graph=s.graph,
                fingerprint=s.fingerprint,
                complexity_metrics=baseline_complexity,
                evaluation_metrics=s.evaluation_metrics,
                constraints_status=status_map
            )
            if is_valid:
                filtered_candidates.append(s_updated)

        trace_recorder.record_stage(
            "constraint_filtering",
            input_summary={"total_candidates": len(all_candidates)},
            output_summary={"valid_candidates": [s.name for s in filtered_candidates]}
        )

        if not filtered_candidates:
            raise ValueError("All generated planning strategies violated environment constraints! No viable plan.")

        # Stage 4: Strategy Evaluation
        evaluated_candidates = []
        for s in filtered_candidates:
            eval_metrics = self.evaluator.evaluate(intent, s.graph)
            s_evaluated = PlanningStrategy(
                name=s.name,
                policy=s.policy,
                graph=s.graph,
                fingerprint=s.fingerprint,
                complexity_metrics=baseline_complexity,
                evaluation_metrics=eval_metrics,
                constraints_status=s.constraints_status
            )
            evaluated_candidates.append(s_evaluated)

        trace_recorder.record_stage(
            "strategy_evaluation",
            input_summary={"evaluated_count": len(evaluated_candidates)},
            output_summary={s.name: s.evaluation_metrics.utility_score for s in evaluated_candidates}
        )

        # Stage 5: Strategy Ranking
        ranked_candidates = self.ranker.rank(evaluated_candidates)
        
        trace_recorder.record_stage(
            "strategy_ranking",
            input_summary={"ranking_inputs": [s.name for s in evaluated_candidates]},
            output_summary={"ranked_order": [s.name for s in ranked_candidates]}
        )

        # Stage 6: Strategy Selection
        decision = self.selector.select(ranked_candidates)
        selected_strategy = ranked_candidates[0]
        
        trace_recorder.record_stage(
            "strategy_selection",
            input_summary={"highest_utility": selected_strategy.name},
            output_summary={"selected": decision.selected_strategy_name, "confidence": decision.selection_confidence}
        )

        # Cache the successful graph
        if not cached_graph:
            self.memory.store(intent, context, selected_strategy.graph)

        planning_duration_ms = (time.perf_counter() - t0) * 1000.0

        # Compile trace
        trace = trace_recorder.compile(
            all_strategies=all_candidates,
            filtered_strategies=filtered_candidates,
            ranked_strategies=ranked_candidates,
            selected_name=selected_strategy.name,
            duration_ms=planning_duration_ms
        )

        return selected_strategy.graph, trace, decision
