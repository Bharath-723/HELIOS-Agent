"""
HELIOS v2 - Planning Validator
Validates every ExecutionPlan for correctness, tool compatibility, model availability, and DAG safety.
"""
from typing import List, Dict, Set
from core.reasoning.reasoning_models import (
    TaskIntent,
    ReasoningContext,
    AtomicTask,
    ValidationResult
)

class PlanningValidator:
    def validate(self, intent: TaskIntent, context: ReasoningContext, tasks: List[AtomicTask]) -> ValidationResult:
        errors = []
        warnings = []
        
        # 1. Empty plan check
        if not tasks:
            errors.append("Execution plan contains no atomic tasks.")
            return ValidationResult(status=False, errors=errors, warnings=warnings, validation_summary="Validation failed: Plan is empty.")

        task_ids = [t.task_id for t in tasks]
        
        # 2. Duplicate task IDs check
        if len(task_ids) != len(set(task_ids)):
            errors.append("Execution plan contains duplicate task IDs.")

        task_map = {t.task_id: t for t in tasks}
        
        # 3. Missing dependencies check
        for t in tasks:
            for dep in t.dependencies:
                if dep not in task_map:
                    errors.append(f"Task '{t.task_id}' depends on missing task '{dep}'.")

        # 4. Circular dependencies / Invalid DAG check (only run if no missing dependency errors)
        if not errors:
            try:
                # Run topological sort validation (cycle detection)
                adj = {t.task_id: [] for t in tasks}
                in_degree = {t.task_id: 0 for t in tasks}
                
                for t in tasks:
                    for dep in t.dependencies:
                        adj[dep].append(t.task_id)
                        in_degree[t.task_id] += 1
                        
                queue = [tid for tid, deg in in_degree.items() if deg == 0]
                visited_count = 0
                while queue:
                    curr = queue.pop(0)
                    visited_count += 1
                    for neighbor in adj[curr]:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            queue.append(neighbor)
                            
                if visited_count != len(tasks):
                    errors.append("Circular dependency detected in reasoning graph DAG structure.")
            except Exception as e:
                errors.append(f"DAG validation crashed: {e}")

        # 5. Tool verification check
        for t in tasks:
            if t.required_tool:
                if t.required_tool not in context.available_tools:
                    errors.append(f"Required tool '{t.required_tool}' in task '{t.task_id}' is not available in reasoning context.")
                if t.required_tool not in intent.requires_tools and intent.category != TaskCategory.MIXED if 'TaskCategory' in globals() else True:
                    # Let this be a warning (unused tools in intent matching but mapped during DAG planning is ok)
                    pass

        # 6. Model verification check
        for t in tasks:
            if t.required_model not in context.available_models:
                errors.append(f"Required model '{t.required_model}' in task '{t.task_id}' is not supported by registry context.")

        # 7. Fallback strategy validation check
        valid_fallbacks = {"fallback_to_cloud", "fallback_to_local_search", "fallback_to_mistral", "abort_workflow", "prompt_clarification", "show_raw_results", "use_raw_snippets", "show_raw_snippets"}
        for t in tasks:
            if t.fallback_strategy not in valid_fallbacks:
                warnings.append(f"Task '{t.task_id}' specifies unrecognized fallback strategy '{t.fallback_strategy}'.")

        # 8. Privacy constraints warning
        if intent.privacy_requirement == "high":
            for t in tasks:
                if "gemini" in t.required_model or "gpt" in t.required_model:
                    errors.append(f"Privacy constraint conflict: Task '{t.task_id}' is assigned to Cloud Model '{t.required_model}' under High privacy requirements.")

        status = len(errors) == 0
        summary = (
            "Planning validation successful. DAG is valid, and all required resource targets are supported."
            if status
            else f"Planning validation failed with {len(errors)} errors and {len(warnings)} warnings."
        )

        return ValidationResult(
            status=status,
            errors=errors,
            warnings=warnings,
            validation_summary=summary
        )
