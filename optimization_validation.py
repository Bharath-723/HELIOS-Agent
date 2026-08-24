"""
HELIOS v2 - Plan Optimization Validation Suite
Verifies dependency pruning, parallel merging, model substitution, equivalence validation, and deterministic convergence.
"""
import os
import sys
import logging

sys.path.insert(0, os.path.abspath('.'))

from core.reasoning import ReasoningContext, AtomicTask, ExecutionGraph, TaskCategory, TaskIntent, TaskUnderstanding
from core.reasoning.context_builder import ContextBuilder
from core.reasoning.reasoning_engine import ReasoningEngine
from core.reasoning.plan_optimizer import PlanOptimizer
from core.reasoning.dependency_optimizer import DependencyOptimizer
from core.reasoning.parallel_optimizer import ParallelOptimizer
from core.reasoning.resource_optimizer import ResourceOptimizer
from core.reasoning.plan_refiner import PlanRefiner

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("helios.reasoning.optimization.validation")

def run_optimization_validation():
    log.info("Starting HELIOS v2 Plan Optimization Validation...")
    
    engine = ReasoningEngine()
    cb = ContextBuilder()
    context = cb.build(internet_available=True, local_model_available=True)
    context.hardware_specs["low_ram_mode"] = False
    
    # ---------------------------------------------------------
    # Test 1: Dependency Optimizer (Transitive Pruning)
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 1: Transitive Dependency Pruning")
    dep_opt = DependencyOptimizer()
    
    # Task 3 depends on Task 2 and Task 1. Task 2 depends on Task 1.
    # Therefore, Task 3 -> Task 1 is redundant.
    t1 = AtomicTask("task_1", "Start Task", "out_1", None, "gemma3", "abort", 0.0, 100.0, 0.0)
    t2 = AtomicTask("task_2", "Middle Task", "out_2", None, "gemma3", "abort", 0.0, 100.0, 0.0, dependencies=["task_1"])
    t3 = AtomicTask("task_3", "End Task", "out_3", None, "gemma3", "abort", 0.0, 100.0, 0.0, dependencies=["task_2", "task_1"])
    
    optimized_tasks = dep_opt.optimize([t1, t2, t3])
    t3_opt = next(t for t in optimized_tasks if t.task_id == "task_3")
    
    assert "task_1" not in t3_opt.dependencies, "Transitive dependency task_1 was not pruned from task_3!"
    assert "task_2" in t3_opt.dependencies
    log.info("  ✓ Transitive dependency pruned successfully (Task 3 depends only on Task 2)")

    # ---------------------------------------------------------
    # Test 2: Parallel Optimizer (Merging Artificial Sequences)
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 2: Artificial Dependency Parallelization")
    par_opt = ParallelOptimizer()
    
    # Notes save depending on network connectivity check is artificial
    t_conn = AtomicTask("task_1", "Verify internet connectivity status", "conn", None, "gemma3", "abort", 0.0, 100.0, 0.0)
    t_notes = AtomicTask("task_2", "Save to notes folder", "notes_save", "NotesManager", "gemma3", "abort", 0.0, 500.0, 0.2, dependencies=["task_1"])
    
    opt_parallel = par_opt.optimize([t_conn, t_notes])
    t_notes_opt = next(t for t in opt_parallel if t.task_id == "task_2")
    
    assert "task_1" not in t_notes_opt.dependencies, "Artificial dependency task_1 was not parallelized!"
    log.info("  ✓ Artificial sequential dependency pruned, allowing parallel execution")

    # ---------------------------------------------------------
    # Test 3: Resource Optimizer (Model Substitution)
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 3: Model Substitution for Resource Savings")
    res_opt = ResourceOptimizer()
    
    # Task 1 uses gemma3, Task 2 uses mistral. Standardize on mistral to avoid loading both.
    t_gemma = AtomicTask("task_1", "First task", "out", None, "gemma3", "abort", 0.0, 100.0, 0.0)
    t_mistral = AtomicTask("task_2", "Second task", "out", None, "mistral", "abort", 0.0, 200.0, 0.0)
    
    opt_resources = res_opt.optimize([t_gemma, t_mistral])
    t1_opt = next(t for t in opt_resources if t.task_id == "task_1")
    t2_opt = next(t for t in opt_resources if t.task_id == "task_2")
    
    assert t1_opt.required_model == "mistral", f"Model substitution failed, expected mistral got {t1_opt.required_model}"
    assert t2_opt.required_model == "mistral"
    log.info("  ✓ Weaker model substituted with stronger model (gemma3 -> mistral) to prevent thrashing")

    # ---------------------------------------------------------
    # Test 4: Equivalence Verification
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 4: Semantic Plan Equivalence Verification")
    refiner = PlanRefiner()
    
    # Drop a vital note saving task and expect verification failure
    t_save = AtomicTask("task_save", "Save final note content", "save_conf", "NotesManager", "gemma3", "abort", 0.0, 100.0, 0.0)
    is_equiv, reason = refiner.verify_equivalence([t_save], [])
    assert is_equiv == False
    assert "Vital task" in reason
    log.info("  ✓ Dropping vital tasks correctly blocked by equivalence verifier: '%s'", reason)

    # ---------------------------------------------------------
    # Test 5: Plan Optimizer Loop (Convergence and Rollback)
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 5: Central Optimizer Loop & Rollback logic")
    optimizer = PlanOptimizer()
    
    prompt = "Search online for the latest Python 3.12 updates and append note to my notes folder."
    plan = engine.plan(prompt, context)
    
    # Check that optimization trace metrics exist
    assert plan.optimization_trace is not None
    opt_metrics = plan.optimization_trace.metrics
    log.info("  ✓ Baseline Utility: %.4f, Optimized Utility: %.4f", plan.optimization_trace.original_utility, plan.optimization_trace.final_utility)
    log.info("  ✓ Utility Improvement Gain: %.4f", opt_metrics.utility_improvement)
    log.info("  ✓ Latency Reduction: %.2fms", opt_metrics.latency_reduction_ms)
    log.info("  ✓ Dependency Count Reduced by: %d", opt_metrics.dependency_reduction)
    
    # Verify rollback condition: Mock a refiner that decreases plan utility, and ensure it rolls back
    original_graph = plan.graph
    from unittest.mock import patch, MagicMock
    from core.reasoning.strategy_evaluator import StrategyEvaluation
    
    mock_refined_graph = MagicMock(spec=ExecutionGraph)
    mock_refined_graph.tasks = original_graph.tasks.copy()
    mock_refined_graph.tasks["mock_task"] = AtomicTask("mock_task", "mock", "mock", None, "gemma3", "abort", 0.0, 100.0, 0.0)
    
    with patch.object(optimizer.refiner, 'refine', return_value=(mock_refined_graph, "Mock optimization")), \
         patch.object(optimizer, '_get_fingerprint', side_effect=["fingerprint_1", "fingerprint_2", "fingerprint_3"]), \
         patch.object(optimizer.evaluator, 'evaluate') as mock_eval:
         
        # Initial call returns 0.8, next call returns 0.4 (worse utility)
        mock_eval.side_effect = [
            StrategyEvaluation(cost=0.0, latency=100.0, complexity=0.5, parallel_efficiency=0.5, failure_probability=0.2, privacy_score=0.5, tool_utilization=0.5, utility_score=0.8),
            StrategyEvaluation(cost=0.0, latency=100.0, complexity=0.5, parallel_efficiency=0.5, failure_probability=0.2, privacy_score=0.5, tool_utilization=0.5, utility_score=0.4)
        ]
        
        intent = engine.intent_engine.parse(prompt)
        opt_graph, opt_trace = optimizer.optimize_plan(intent, context, original_graph)
        
        # Iteration 1 node should record the rollback decision
        assert opt_trace.history[-1].decision_taken == "Rollback applied (Utility decreased)."
        log.info("  ✓ Automatic rollback correctly triggered when utility decreases")

    log.info("\n==================================================")
    log.info("HELIOS v2 Plan Optimization Validation: SUCCESS")

if __name__ == '__main__':
    run_optimization_validation()
