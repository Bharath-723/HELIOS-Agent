"""
HELIOS v2 - Plan Explanation Engine
Generates detailed structured explanations for planning decisions, tool/model choices, and dependencies.
"""
from typing import List, Dict
from core.reasoning.reasoning_models import TaskIntent, TaskUnderstanding, AtomicTask, PlanExplanation

class PlanExplanationEngine:
    def explain(self, intent: TaskIntent, understanding: TaskUnderstanding, tasks: List[AtomicTask]) -> PlanExplanation:
        why_tasks_exist = {}
        why_ordering_exists = []
        why_dependencies_exist = {}
        why_tools_selected = {}
        why_models_suggested = {}

        # 1. Why tasks exist
        for t in tasks:
            why_tasks_exist[t.task_id] = (
                f"Task '{t.description}' was created to satisfy the "
                f"goal of category '{intent.category.value}' demanding output format '{t.expected_output}'."
            )

        # 2. Why dependencies exist
        for t in tasks:
            if t.dependencies:
                why_dependencies_exist[t.task_id] = t.dependencies.copy()
                deps_str = ", ".join(t.dependencies)
                why_ordering_exists.append(
                    f"Task '{t.task_id}' must wait for completion of [{deps_str}] because it requires their outputs as preconditions."
                )
            else:
                why_ordering_exists.append(
                    f"Task '{t.task_id}' has no dependencies and can execute immediately at Level 0."
                )

        # 3. Why internet required
        why_internet = (
            "Internet access was required because the task demands real-time/fresh external data source queries."
            if intent.requires_internet
            else "Internet access was disabled to enforce local sandbox boundaries and offline data confidentiality."
        )

        # 4. Why privacy required
        why_privacy = (
            f"Privacy requirement was classified as '{intent.privacy_requirement}' because the query "
            f"matches sensitive data keywords or notes/file operations."
        )

        # 5. Why tools and models were selected
        for t in tasks:
            if t.required_tool:
                why_tools_selected[t.task_id] = (
                    f"Tool '{t.required_tool}' was chosen because it provides deterministic "
                    f"capabilities for expected output type '{t.expected_output}'."
                )
            else:
                why_tools_selected[t.task_id] = "No deterministic tool needed; handled via standard LLM cognitive inference."

            why_models_suggested[t.task_id] = (
                f"Model '{t.required_model}' was selected to balance task complexity "
                f"(scored {intent.complexity_score:.2f}) with latency and privacy constraints."
            )

        return PlanExplanation(
            why_tasks_exist=why_tasks_exist,
            why_ordering_exists=why_ordering_exists,
            why_dependencies_exist=why_dependencies_exist,
            why_internet_required=why_internet,
            why_privacy_required=why_privacy,
            why_tools_selected=why_tools_selected,
            why_models_suggested=why_models_suggested
        )
