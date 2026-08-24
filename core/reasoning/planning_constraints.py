"""
HELIOS v2 - Planning Constraints Evaluator
Classifies task actions against context states using multi-level severity: Allowed, Preferred, Discouraged, Forbidden.
"""
from typing import Dict, List, Tuple
from core.reasoning.reasoning_models import (
    TaskIntent,
    ReasoningContext,
    AtomicTask,
    ConstraintSeverity
)

class PlanningConstraintEvaluator:
    def evaluate_constraints(
        self, intent: TaskIntent, context: ReasoningContext, tasks: List[AtomicTask]
    ) -> Tuple[bool, Dict[str, ConstraintSeverity]]:
        """
        Evaluates tasks against context parameters.
        Returns:
            - is_valid: bool (True if no constraints are FORBIDDEN)
            - status_map: Dict[str, ConstraintSeverity] mapping constraint names to severity.
        """
        status_map = {}
        is_valid = True

        # 1. Offline Mode Constraint
        has_network_task = any(t.required_tool == "WebSearch" for t in tasks)
        if not context.internet_available and has_network_task:
            status_map["network_availability"] = ConstraintSeverity.FORBIDDEN
            is_valid = False
        elif context.internet_available and has_network_task:
            status_map["network_availability"] = ConstraintSeverity.ALLOWED
        else:
            status_map["network_availability"] = ConstraintSeverity.PREFERRED

        # 2. Privacy Confinement Constraint
        has_cloud_model = any("gemini" in t.required_model or "gpt" in t.required_model for t in tasks)
        if intent.privacy_requirement == "high" and has_cloud_model:
            status_map["privacy_confinement"] = ConstraintSeverity.FORBIDDEN
            is_valid = False
        elif intent.privacy_requirement == "high" and not has_cloud_model:
            status_map["privacy_confinement"] = ConstraintSeverity.PREFERRED
        elif intent.privacy_requirement == "medium" and has_cloud_model:
            status_map["privacy_confinement"] = ConstraintSeverity.DISCOURAGED
        else:
            status_map["privacy_confinement"] = ConstraintSeverity.ALLOWED

        # 3. Tool Presence Constraint
        for t in tasks:
            if t.required_tool and t.required_tool not in context.available_tools:
                status_map[f"tool_presence_{t.required_tool}"] = ConstraintSeverity.FORBIDDEN
                is_valid = False
            elif t.required_tool:
                status_map[f"tool_presence_{t.required_tool}"] = ConstraintSeverity.ALLOWED

        # 4. Model Presence Constraint
        for t in tasks:
            if t.required_model not in context.available_models:
                status_map[f"model_presence_{t.required_model}"] = ConstraintSeverity.FORBIDDEN
                is_valid = False
            elif not context.local_model_available and t.required_model in ("gemma3", "mistral"):
                status_map[f"model_presence_{t.required_model}"] = ConstraintSeverity.FORBIDDEN
                is_valid = False
            else:
                status_map[f"model_presence_{t.required_model}"] = ConstraintSeverity.ALLOWED

        # 5. Resource Constraint (Low RAM mode)
        if context.hardware_specs.get("low_ram_mode", False):
            # Discourage local heavy model if low RAM
            has_heavy_local = any(t.required_model == "mistral" for t in tasks)
            if has_heavy_local:
                status_map["memory_overhead"] = ConstraintSeverity.DISCOURAGED
            else:
                status_map["memory_overhead"] = ConstraintSeverity.PREFERRED
        else:
            status_map["memory_overhead"] = ConstraintSeverity.ALLOWED

        return is_valid, status_map
