"""
HELIOS v2 - Cognitive Planning Engine Validation Suite
Verifies standard scenarios and comprehensive negative/boundary edge cases.
"""
import os
import sys
import logging

sys.path.insert(0, os.path.abspath('.'))

from core.reasoning.reasoning_models import TaskCategory, TaskState, AtomicTask
from core.reasoning.context_builder import ContextBuilder
from core.reasoning.reasoning_engine import ReasoningEngine
from core.reasoning.planning_validator import PlanningValidator
from core.reasoning.execution_graph_builder import ExecutionGraphBuilder

# Setup basic logging to console
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("helios.reasoning.validation")

def run_test_cases():
    log.info("Starting HELIOS v2 Cognitive Planning Engine Validation...")
    
    # 1. Initialize engine and helper classes
    engine = ReasoningEngine()
    validator = PlanningValidator()
    graph_builder = ExecutionGraphBuilder()
    
    # 2. Compile baseline context
    cb = ContextBuilder()
    cb.add_history("user", "Hello")
    cb.add_history("helios", "Hello there!")
    cb.add_memory("User likes local database execution")
    
    context_online = cb.build(internet_available=True, local_model_available=True)
    context_online.hardware_specs["low_ram_mode"] = False
    
    context_offline = cb.build(internet_available=False, local_model_available=True)
    context_offline.hardware_specs["low_ram_mode"] = False
    
    context_low_ram = cb.build(internet_available=True, local_model_available=True)
    context_low_ram.hardware_specs["low_ram_mode"] = True

    # =========================================================
    # PART 1: Standard Scenarios (Sprint 1 Verification)
    # =========================================================
    standard_cases = [
        {
            "name": "Simple Chat",
            "prompt": "Hi, tell me a short story about antigravity.",
            "expected_category": TaskCategory.CHAT,
            "expected_task_count": 1,
            "expected_requires_internet": False,
            "expected_privacy": "low"
        },
        {
            "name": "Web Search",
            "prompt": "Search online for the latest news about Space Exploration.",
            "expected_category": TaskCategory.SEARCH,
            "expected_task_count": 3,
            "expected_requires_internet": True,
            "expected_privacy": "low"
        },
        {
            "name": "File Creation",
            "prompt": "Create a file named resume_template.docx with basic sections.",
            "expected_category": TaskCategory.FILE,
            "expected_task_count": 2,
            "expected_requires_internet": False,
            "expected_privacy": "medium"
        },
        {
            "name": "Scheduling",
            "prompt": "Schedule a reminder in 15 minutes to pay college fees.",
            "expected_category": TaskCategory.SCHEDULE,
            "expected_task_count": 2,
            "expected_requires_internet": False,
            "expected_privacy": "low"
        },
        {
            "name": "Privacy Task",
            "prompt": "Here is my bank personal password: secret123, keep it safe.",
            "expected_category": TaskCategory.PRIVACY_TASK,
            "expected_task_count": 1,
            "expected_requires_internet": False,
            "expected_privacy": "high"
        },
        {
            "name": "Mixed / Multi-step Workflow",
            "prompt": "Search online for the latest news about Python 3.12 and save note to my notes folder.",
            "expected_category": TaskCategory.MIXED,
            "expected_task_count": 4,
            "expected_requires_internet": True,
            "expected_privacy": "medium"
        }
    ]

    for tc in standard_cases:
        log.info("\n--------------------------------------------------")
        log.info("Standard Case: %s", tc["name"])
        plan = engine.plan(tc["prompt"], context_online)
        
        # Validations
        assert plan.intent.category == tc["expected_category"]
        assert plan.intent.requires_internet == tc["expected_requires_internet"]
        assert plan.intent.privacy_requirement == tc["expected_privacy"]
        assert len(plan.graph.tasks) == tc["expected_task_count"]
        assert plan.validation_result.status == True, f"Expected successful validation, got errors: {plan.validation_result.errors}"
        assert plan.complexity_metrics["total_estimated_latency_ms"] > 0
        assert plan.explanation.why_internet_required is not None
        
        # Verify DAG levels
        for tid in plan.graph.execution_order:
            task = plan.graph.tasks[tid]
            for dep in task.dependencies:
                assert plan.graph.execution_order.index(dep) < plan.graph.execution_order.index(tid)
                
        log.info("  ✓ Plan Validated successfully. Time: %.2fms. Complexity: %s", plan.planning_time_ms, plan.complexity_metrics)

    # =========================================================
    # PART 2: Negative & Boundary Edge Cases (Sprint 1.5)
    # =========================================================
    log.info("\n==================================================")
    log.info("Running Sprint 1.5 Architecture Hardening Edge Cases...")

    # Case 2.1: Empty and Invalid Prompts
    log.info("\n--------------------------------------------------")
    log.info("Edge Case 2.1: Empty and Whitespace prompts")
    for empty_p in ["", "   ", "\n\t"]:
        empty_plan = engine.plan(empty_p, context_online)
        # Should default to chat category but validate successfully (with empty tasks warning/error if planner yielded empty)
        # Note: TaskPlanner will generate at least a Chat Task for empty prompt, so it passes validation
        assert empty_plan.intent.category == TaskCategory.CHAT
        assert empty_plan.validation_result.status == True
        log.info("  ✓ Empty prompt handled safely. Category: %s", empty_plan.intent.category.name)

    # Case 2.2: Circular Dependency Detection
    log.info("\n--------------------------------------------------")
    log.info("Edge Case 2.2: Circular Dependency DAG Validation")
    t1 = AtomicTask("task_1", "Step 1", "output_1", None, "gemma3", "abort_workflow", 0.0, 100.0, 0.0, dependencies=["task_2"])
    t2 = AtomicTask("task_2", "Step 2", "output_2", None, "gemma3", "abort_workflow", 0.0, 100.0, 0.0, dependencies=["task_1"])
    
    try:
        graph_builder.build_graph([t1, t2])
        assert False, "Expected ValueError during circular dependency building"
    except ValueError as val_err:
        assert "Circular dependency" in str(val_err)
        log.info("  ✓ Circular dependency caught by Graph Builder: '%s'", val_err)

    # Case 2.3: Missing Dependency Validation
    log.info("\n--------------------------------------------------")
    log.info("Edge Case 2.3: Missing Dependency ID validation")
    t_missing_dep = AtomicTask("task_1", "Step 1", "output_1", None, "gemma3", "abort_workflow", 0.0, 100.0, 0.0, dependencies=["missing_task_id"])
    intent_mock = engine.intent_engine.parse("dummy text")
    
    val_res = validator.validate(intent_mock, context_online, [t_missing_dep])
    assert val_res.status == False
    assert any("depends on missing task" in err for err in val_res.errors)
    log.info("  ✓ Missing dependency caught by Validator: %s", val_res.errors)

    # Case 2.4: Unknown Tool Validation
    log.info("\n--------------------------------------------------")
    log.info("Edge Case 2.4: Unknown Tool validation")
    t_unknown_tool = AtomicTask("task_1", "Step 1", "output_1", "SuperQuantumTool", "gemma3", "abort_workflow", 0.0, 100.0, 0.0)
    val_res = validator.validate(intent_mock, context_online, [t_unknown_tool])
    assert val_res.status == False
    assert any("SuperQuantumTool" in err for err in val_res.errors)
    log.info("  ✓ Unknown tool caught by Validator: %s", val_res.errors)

    # Case 2.5: Unknown Model Validation
    log.info("\n--------------------------------------------------")
    log.info("Edge Case 2.5: Unknown Model validation")
    t_unknown_model = AtomicTask("task_1", "Step 1", "output_1", None, "llama-42b-super", "abort_workflow", 0.0, 100.0, 0.0)
    val_res = validator.validate(intent_mock, context_online, [t_unknown_model])
    assert val_res.status == False
    assert any("llama-42b-super" in err for err in val_res.errors)
    log.info("  ✓ Unknown model caught by Validator: %s", val_res.errors)

    # Case 2.6: Privacy Conflict Validation
    log.info("\n--------------------------------------------------")
    log.info("Edge Case 2.6: Privacy constraint mapping validation")
    # Prompt is high privacy, but task is assigned to gemini cloud model
    intent_privacy = engine.intent_engine.parse("Here is my secret salary details and password")
    t_cloud = AtomicTask("task_1", "Process password details", "text", None, "gemini-2.0-flash", "abort_workflow", 0.0, 100.0, 0.0)
    val_res = validator.validate(intent_privacy, context_online, [t_cloud])
    assert val_res.status == False
    assert any("Privacy constraint conflict" in err for err in val_res.errors)
    log.info("  ✓ Privacy vs Cloud model conflict successfully blocked: %s", val_res.errors)

    # Case 2.7: Contradictory Objectives (Privacy constraints vs Online Search requests)
    log.info("\n--------------------------------------------------")
    log.info("Edge Case 2.7: Contradictory Objectives (Search + Password)")
    contradictory_prompt = "Search online for the latest weather, and save my secret password credentials to notes."
    plan_contra = engine.plan(contradictory_prompt, context_online)
    # The intent understanding engine should capture BOTH requirements:
    # Requires internet is True, but privacy requirement is escalated to High/Medium due to credentials/notes.
    assert plan_contra.intent.requires_internet == True
    assert plan_contra.intent.privacy_requirement in ("high", "medium")
    log.info("  ✓ Contradictory objectives classified safely. Internet: %s, Privacy: %s", plan_contra.intent.requires_internet, plan_contra.intent.privacy_requirement)

    log.info("\n==================================================")
    log.info("HELIOS v2 Cognitive Planning Engine Validation: SUCCESS")

if __name__ == '__main__':
    run_test_cases()
