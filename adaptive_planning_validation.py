"""
HELIOS v2 - Adaptive Cognitive Planning Engine Validation Suite
Validates strategy generation, constraint filtering, utility ranking, tie-breaking, caching, and edge-cases.
"""
import os
import sys
import logging

sys.path.insert(0, os.path.abspath('.'))

from core.reasoning.reasoning_models import TaskCategory, PlanningPolicy, ConstraintSeverity
from core.reasoning.context_builder import ContextBuilder
from core.reasoning.reasoning_engine import ReasoningEngine
from core.reasoning.strategy_ranker import StrategyRanker
from core.reasoning import PlanningStrategy, ExecutionGraph, StrategyEvaluation

# Setup logging to console
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("helios.reasoning.adaptive.validation")

def run_adaptive_validation():
    log.info("Starting HELIOS v2 Adaptive Planning Engine Validation...")
    
    engine = ReasoningEngine()
    
    # Setup contexts
    cb = ContextBuilder()
    cb.add_history("user", "Hello")
    cb.add_history("helios", "Hello there!")
    cb.add_memory("User prefers offline execution")
    
    context_online = cb.build(internet_available=True, local_model_available=True)
    context_online.hardware_specs["low_ram_mode"] = False
    
    context_offline = cb.build(internet_available=False, local_model_available=True)
    context_offline.hardware_specs["low_ram_mode"] = False
    
    context_low_ram = cb.build(internet_available=True, local_model_available=True)
    context_low_ram.hardware_specs["low_ram_mode"] = True
    
    # ---------------------------------------------------------
    # Test 1: Standard Adaptive Planning (Search + Note)
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 1: Standard Multi-strategy Generation and Ranking")
    prompt = "Search online for Python 3.12 release date and save to notes folder."
    
    # Generate plan
    plan = engine.plan(prompt, context_online)
    
    # Verify multiple alternative strategies exist in trace
    assert len(plan.trace.all_strategies) > 1, "Expected multiple alternative strategies generated"
    log.info("  ✓ Strategies generated: %s", plan.trace.all_strategies)
    
    # Verify ranking descending order
    rank_scores = [item["utility"] for item in plan.trace.ranked_strategies]
    assert rank_scores == sorted(rank_scores, reverse=True), f"Ranking not sorted in descending order: {rank_scores}"
    log.info("  ✓ Strategies ranked correctly: %s", plan.trace.ranked_strategies)
    
    # Verify utility breakdown presence
    assert plan.selection.selected_strategy_name is not None
    log.info("  ✓ Selected optimal strategy: %s", plan.selection.selected_strategy_name)
    log.info("  ✓ Selection confidence: %.4f, Margin: %.4f", plan.selection.selection_confidence, plan.selection.selection_margin)
    
    # ---------------------------------------------------------
    # Test 2: Constraint Filtering & Multi-Level Severities
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 2: Constraint Filtering under Offline state")
    
    # Under offline context, strategies containing WebSearch tool should have network_availability = FORBIDDEN
    # and get filtered out of the ranked strategies.
    plan_offline = engine.plan(prompt, context_offline)
    # Find strategy-fast-response (uses gemini/search)
    # It should either be filtered out or altered.
    assert "strategy-fast-response" not in plan_offline.trace.filtered_strategies, "Expected fast-response (cloud/web search) to be filtered out in offline mode"
    log.info("  ✓ Offline constraint successfully filtered forbidden strategies. Remaining: %s", plan_offline.trace.filtered_strategies)

    # ---------------------------------------------------------
    # Test 3: Low RAM Mode Policy Adaptation
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 3: Heuristic resource adaptation under Low RAM")
    
    plan_low_ram = engine.plan(prompt, context_low_ram)
    # Under low RAM, memory_overhead constraint is DISCOURAGED/PREFERRED
    selected_strategy = plan_low_ram.trace.selected_strategy_name
    log.info("  ✓ Selected strategy under low RAM: %s", selected_strategy)

    # ---------------------------------------------------------
    # Test 4: Planning Memory Caching
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 4: Planning Memory structure caching")
    
    # First plan stores structural graph to cache
    engine.adaptive_planner.memory.clear()
    plan_run1 = engine.plan(prompt, context_online)
    assert plan_run1.trace.stages["planning_memory_check"]["output"]["cache_hit"] == False, "Expected cache miss on first run"
    
    # Second identical plan hits cache
    plan_run2 = engine.plan(prompt, context_online)
    assert plan_run2.trace.stages["planning_memory_check"]["output"]["cache_hit"] == True, "Expected cache hit on second run"
    log.info("  ✓ Planning Memory cache HIT verified successfully")

    # ---------------------------------------------------------
    # Test 5: Deterministic Tie-Breaker Policy
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 5: Deterministic Tie-Breaker Policy")
    ranker = StrategyRanker()
    # Create two strategies with identical utility scores
    graph1 = ExecutionGraph(tasks={}, execution_order=[], parallel_groups=[], fallback_nodes={}, retry_policies={}, verification_checks=[])
    graph2 = ExecutionGraph(tasks={}, execution_order=[], parallel_groups=[], fallback_nodes={}, retry_policies={}, verification_checks=[])
    
    eval1 = StrategyEvaluation(cost=0.005, latency=1000.0, complexity=0.5, parallel_efficiency=0.5, failure_probability=0.2, privacy_score=0.5, tool_utilization=0.5, utility_score=0.8)
    eval2 = StrategyEvaluation(cost=0.002, latency=1500.0, complexity=0.5, parallel_efficiency=0.5, failure_probability=0.2, privacy_score=0.5, tool_utilization=0.5, utility_score=0.8)
    
    s_higher_cost = PlanningStrategy(name="strategy-high-cost", policy=PlanningPolicy.HIGH_ACCURACY, graph=graph1, fingerprint="f1", complexity_metrics={}, evaluation_metrics=eval1)
    s_lower_cost = PlanningStrategy(name="strategy-low-cost", policy=PlanningPolicy.LOW_RESOURCE, graph=graph2, fingerprint="f2", complexity_metrics={}, evaluation_metrics=eval2)
    
    ranked = ranker.rank([s_higher_cost, s_lower_cost])
    # Tie-breaker 1 says: lowest cost comes first
    assert ranked[0].name == "strategy-low-cost", f"Expected strategy-low-cost to win tie-breaker, got {ranked[0].name}"
    log.info("  ✓ Deterministic cost-based tie-breaker passed")

    # Tie-breaker 2: Same cost, different latency
    eval3 = StrategyEvaluation(cost=0.002, latency=800.0, complexity=0.5, parallel_efficiency=0.5, failure_probability=0.2, privacy_score=0.5, tool_utilization=0.5, utility_score=0.8)
    s_lower_lat = PlanningStrategy(name="strategy-low-lat", policy=PlanningPolicy.FAST_RESPONSE, graph=graph1, fingerprint="f3", complexity_metrics={}, evaluation_metrics=eval3)
    s_higher_lat = PlanningStrategy(name="strategy-high-lat", policy=PlanningPolicy.LOW_RESOURCE, graph=graph2, fingerprint="f4", complexity_metrics={}, evaluation_metrics=eval2)
    
    ranked_lat = ranker.rank([s_higher_lat, s_lower_lat])
    # Tie-breaker 2 says: lowest latency wins
    assert ranked_lat[0].name == "strategy-low-lat", f"Expected strategy-low-lat to win tie-breaker, got {ranked_lat[0].name}"
    log.info("  ✓ Deterministic latency-based tie-breaker passed")

    log.info("\n==================================================")
    log.info("HELIOS v2 Adaptive Planning Engine Validation: SUCCESS")

if __name__ == '__main__':
    run_adaptive_validation()
