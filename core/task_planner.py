"""
core/task_planner.py — HELIOS Goal Decomposition & Multi-Step Task Planner
========================================================================
Decomposes complex user goals into atomic execution steps, maintains step state,
and tracks generated artifacts throughout task execution.
"""

import logging
from typing import List, Dict, Any, Optional

log = logging.getLogger("helios.task_planner")

class TaskStep:
    def __init__(self, step_id: int, description: str, action: str, params: dict):
        self.step_id = step_id
        self.description = description
        self.action = action
        self.params = params
        self.status = "pending"  # pending | in_progress | completed | failed
        self.result: Optional[str] = None

class TaskPlan:
    def __init__(self, goal: str, steps: List[TaskStep]):
        self.goal = goal
        self.steps = steps
        self.current_step_index = 0
        self.status = "planned"  # planned | executing | completed | failed
        self.artifacts: List[str] = []

    def get_current_step(self) -> Optional[TaskStep]:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance(self, result: str, success: bool = True) -> None:
        step = self.get_current_step()
        if step:
            step.result = result
            step.status = "completed" if success else "failed"
            if success and "saved as" in result.lower():
                self.artifacts.append(result)
        
        self.current_step_index += 1
        if self.current_step_index >= len(self.steps):
            self.status = "completed" if all(s.status == "completed" for s in self.steps) else "failed"

class AgenticPlanner:
    """Decomposes compound user requests into structured multi-step TaskPlans."""

    @staticmethod
    def plan_goal(goal: str) -> Optional[TaskPlan]:
        g_lower = goal.lower()
        log.info("Evaluating multi-step goal planning for: '%s'", goal)

        # Multi-step compound goal pattern 1: "find X, summarize it, create file Y"
        if "find" in g_lower and ("summarize" in g_lower or "summary" in g_lower) and ("create" in g_lower or "save" in g_lower or "pdf" in g_lower or "word" in g_lower or "doc" in g_lower):
            steps = [
                TaskStep(1, "Find report file", "find_file", {"query": goal}),
                TaskStep(2, "Summarize content", "general_chat", {"message": "Summarize content"}),
                TaskStep(3, "Create summary document", "create_file", {"name": "summary_report.txt", "location": "desktop", "content": "Summary content"})
            ]
            return TaskPlan(goal, steps)

        # Multi-step industrial MRPL inspection workflow pattern: "inspection report", "sop", "approval note", "word/docx"
        if ("inspection" in g_lower or "report" in g_lower) and ("sop" in g_lower or "compliance" in g_lower) and ("approval" in g_lower or "word" in g_lower or "docx" in g_lower):
            steps = [
                TaskStep(1, "OCR & Document Understanding", "ocr_inspection_report", {"file": "data/demo_samples/scanned_inspection_report.png"}),
                TaskStep(2, "Local RAG SOP Retrieval", "retrieve_sop", {"file": "data/demo_samples/SOP_Plant_Safety_2026.docx"}),
                TaskStep(3, "Reasoning & Compliance Audit", "reason_compliance", {"rule": "Max 400 PSI"}),
                TaskStep(4, "Generate Approval Note & Word Export", "export_approval_docx", {"output": "MRPL_Approval_Note_PSV301.docx"})
            ]
            return TaskPlan(goal, steps)

        return None
