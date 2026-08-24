"""
HELIOS v2 - Planning Logger
Writes structured JSON planning and reasoning traces to standard logger.
"""
import json
import logging
from core.reasoning.reasoning_models import ExecutionPlan

log = logging.getLogger("helios.reasoning.logger")

class PlanningLogger:
    def log_plan(self, plan: ExecutionPlan):
        # Convert plan components to serializable dict
        graph_dict = {
            "execution_order": plan.graph.execution_order,
            "parallel_groups": plan.graph.parallel_groups,
            "verification_checks": plan.graph.verification_checks
        }
        
        intent_dict = {
            "primary_goal": plan.intent.primary_goal,
            "secondary_goal": plan.intent.secondary_goal,
            "category": plan.intent.category.value,
            "privacy_requirement": plan.intent.privacy_requirement,
            "requires_internet": plan.intent.requires_internet,
            "requires_tools": plan.intent.requires_tools,
            "expected_output": plan.intent.expected_output,
            "complexity_score": plan.intent.complexity_score,
            "urgency_level": plan.intent.urgency_level
        }
        
        trace = {
            "plan_id": plan.plan_id,
            "prompt": plan.prompt,
            "intent": intent_dict,
            "graph": graph_dict,
            "planning_time_ms": plan.planning_time_ms,
            "planning_confidence": plan.planning_confidence,
            "decision_path": plan.decision_path_summary,
            "timestamp": plan.created_at
        }
        
        log.info("Planning Event Trace: %s", json.dumps(trace, ensure_ascii=False))
