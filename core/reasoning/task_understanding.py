"""
HELIOS v2 - Task Understanding Engine
Infers execution constraints, resource requirements, and implicit subtasks from high-level user intents.
"""
from typing import Dict, Any, List
from core.reasoning.reasoning_models import TaskIntent, TaskUnderstanding, TaskCategory

class TaskUnderstandingEngine:
    def analyze(self, intent: TaskIntent) -> TaskUnderstanding:
        implicit_tasks = []
        inferred_deps = {}
        required_tools = intent.requires_tools.copy()
        required_resources = ["cpu", "ram"]
        constraints = []
        output_expectations = {"format": intent.expected_output}

        # 1. Infer constraints and resources
        if intent.requires_internet:
            required_resources.append("network")
            constraints.append("requires_active_connectivity")
            
        if intent.privacy_requirement == "high":
            constraints.append("must_execute_on_local_model")
            constraints.append("data_confinement_active")
            
        if intent.urgency_level == "high":
            constraints.append("optimize_for_minimum_latency")

        # 2. Infer implicit tasks and dependencies
        if intent.category == TaskCategory.SEARCH:
            implicit_tasks.append("check_network_availability")
            implicit_tasks.append("query_web_search_api")
            implicit_tasks.append("summarize_evidence_claims")
            inferred_deps = {
                "query_web_search_api": ["check_network_availability"],
                "summarize_evidence_claims": ["query_web_search_api"]
            }
            
        elif intent.category == TaskCategory.FILE:
            implicit_tasks.append("parse_file_path_parameters")
            implicit_tasks.append("execute_disk_file_operation")
            inferred_deps = {
                "execute_disk_file_operation": ["parse_file_path_parameters"]
            }
            
        elif intent.category == TaskCategory.NOTES:
            implicit_tasks.append("generate_formatted_note_content")
            implicit_tasks.append("write_note_to_disk_database")
            inferred_deps = {
                "write_note_to_disk_database": ["generate_formatted_note_content"]
            }
            
        elif intent.category == TaskCategory.SCHEDULE:
            implicit_tasks.append("parse_schedule_time_heuristics")
            implicit_tasks.append("register_background_alarm_job")
            inferred_deps = {
                "register_background_alarm_job": ["parse_schedule_time_heuristics"]
            }
            
        elif intent.category == TaskCategory.PRIVACY_TASK:
            implicit_tasks.append("redact_conventions_and_keys")
            implicit_tasks.append("eval_via_isolated_local_model")
            inferred_deps = {
                "eval_via_isolated_local_model": ["redact_conventions_and_keys"]
            }
            
        elif intent.category == TaskCategory.MIXED:
            # e.g., Search online and save note
            implicit_tasks.append("check_network_availability")
            implicit_tasks.append("query_web_search_api")
            implicit_tasks.append("summarize_evidence_claims")
            implicit_tasks.append("write_note_to_disk_database")
            inferred_deps = {
                "query_web_search_api": ["check_network_availability"],
                "summarize_evidence_claims": ["query_web_search_api"],
                "write_note_to_disk_database": ["summarize_evidence_claims"]
            }
            
        else:
            implicit_tasks.append("compile_standard_chat_reply")

        return TaskUnderstanding(
            implicit_tasks=implicit_tasks,
            inferred_dependencies=inferred_deps,
            required_tools=required_tools,
            required_resources=required_resources,
            execution_constraints=constraints,
            output_expectations=output_expectations
        )
