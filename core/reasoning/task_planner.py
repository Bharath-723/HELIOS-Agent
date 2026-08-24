"""
HELIOS v2 - Task Planner
Decomposes structured intents into sequences of atomic tasks.
"""
from typing import List
from core.reasoning.reasoning_models import TaskIntent, AtomicTask, TaskCategory, TaskState

class TaskPlanner:
    def plan_subtasks(self, intent: TaskIntent) -> List[AtomicTask]:
        subtasks = []
        
        # Scenario 1: Simple chat response
        if intent.category == TaskCategory.CHAT:
            subtasks.append(
                AtomicTask(
                    task_id="task_1",
                    description=f"Generate plain text response to user query: '{intent.primary_goal}'",
                    expected_output="text_response",
                    required_tool=None,
                    required_model="gemma3",
                    fallback_strategy="fallback_to_cloud",
                    estimated_cost=0.0,
                    estimated_latency_ms=3000.0,
                    estimated_risk=0.1
                )
            )
            
        # Scenario 2: Web Search query
        elif intent.category == TaskCategory.SEARCH:
            subtasks.append(
                AtomicTask(
                    task_id="task_1",
                    description=f"Verify internet connectivity for query: '{intent.primary_goal}'",
                    expected_output="connectivity_status",
                    required_tool="DesktopAgent",
                    required_model="gemma3",
                    fallback_strategy="abort_workflow",
                    estimated_cost=0.0,
                    estimated_latency_ms=100.0,
                    estimated_risk=0.0
                )
            )
            subtasks.append(
                AtomicTask(
                    task_id="task_2",
                    description=f"Execute DuckDuckGo search for: '{intent.primary_goal}'",
                    expected_output="raw_search_results",
                    required_tool="WebSearch",
                    required_model="gemini-2.0-flash",
                    fallback_strategy="fallback_to_local_search",
                    estimated_cost=0.005,
                    estimated_latency_ms=2500.0,
                    estimated_risk=0.3,
                    dependencies=["task_1"]
                )
            )
            subtasks.append(
                AtomicTask(
                    task_id="task_3",
                    description="Summarize search results and format response",
                    expected_output="search_results_summary",
                    required_tool=None,
                    required_model="gemini-2.0-flash",
                    fallback_strategy="show_raw_results",
                    estimated_cost=0.002,
                    estimated_latency_ms=1500.0,
                    estimated_risk=0.2,
                    dependencies=["task_2"]
                )
            )

        # Scenario 3: File Management
        elif intent.category == TaskCategory.FILE:
            subtasks.append(
                AtomicTask(
                    task_id="task_1",
                    description=f"Parse file query parameters for: '{intent.primary_goal}'",
                    expected_output="parsed_file_params",
                    required_tool=None,
                    required_model="gemma3",
                    fallback_strategy="prompt_clarification",
                    estimated_cost=0.0,
                    estimated_latency_ms=500.0,
                    estimated_risk=0.1
                )
            )
            subtasks.append(
                AtomicTask(
                    task_id="task_2",
                    description=f"Execute file operation via DesktopAgent on parsed parameters",
                    expected_output="file_operation_status",
                    required_tool="DesktopAgent",
                    required_model="gemma3",
                    fallback_strategy="abort_workflow",
                    estimated_cost=0.0,
                    estimated_latency_ms=1000.0,
                    estimated_risk=0.4,
                    dependencies=["task_1"]
                )
            )

        # Scenario 4: Notes
        elif intent.category == TaskCategory.NOTES:
            subtasks.append(
                AtomicTask(
                    task_id="task_1",
                    description=f"Synthesize note content for: '{intent.primary_goal}'",
                    expected_output="note_content_draft",
                    required_tool=None,
                    required_model="gemma3",
                    fallback_strategy="fallback_to_cloud",
                    estimated_cost=0.0,
                    estimated_latency_ms=1200.0,
                    estimated_risk=0.1
                )
            )
            subtasks.append(
                AtomicTask(
                    task_id="task_2",
                    description="Save note content via NotesManager",
                    expected_output="note_save_confirmation",
                    required_tool="NotesManager",
                    required_model="gemma3",
                    fallback_strategy="abort_workflow",
                    estimated_cost=0.0,
                    estimated_latency_ms=500.0,
                    estimated_risk=0.2,
                    dependencies=["task_1"]
                )
            )

        # Scenario 5: Scheduling
        elif intent.category == TaskCategory.SCHEDULE:
            subtasks.append(
                AtomicTask(
                    task_id="task_1",
                    description=f"Parse schedule trigger time from query: '{intent.primary_goal}'",
                    expected_output="parsed_time_parameters",
                    required_tool=None,
                    required_model="gemma3",
                    fallback_strategy="prompt_clarification",
                    estimated_cost=0.0,
                    estimated_latency_ms=800.0,
                    estimated_risk=0.2
                )
            )
            subtasks.append(
                AtomicTask(
                    task_id="task_2",
                    description="Register scheduled event inside TaskScheduler",
                    expected_output="scheduler_confirmation",
                    required_tool="TaskScheduler",
                    required_model="gemma3",
                    fallback_strategy="abort_workflow",
                    estimated_cost=0.0,
                    estimated_latency_ms=600.0,
                    estimated_risk=0.2,
                    dependencies=["task_1"]
                )
            )

        # Scenario 6: High Privacy Task
        elif intent.category == TaskCategory.PRIVACY_TASK:
            subtasks.append(
                AtomicTask(
                    task_id="task_1",
                    description=f"Process sensitive request locally using offline model: '{intent.primary_goal}'",
                    expected_output="private_response",
                    required_tool=None,
                    required_model="gemma3",
                    fallback_strategy="fallback_to_mistral",
                    estimated_cost=0.0,
                    estimated_latency_ms=4000.0,
                    estimated_risk=0.4
                )
            )

        # Scenario 7: Mixed Workflow / Multi-step
        else:
            # e.g., "Search latest news and save to notes"
            # Decompose into search subtasks then notes subtasks
            subtasks.append(
                AtomicTask(
                    task_id="task_1",
                    description=f"Verify internet connectivity",
                    expected_output="connectivity_status",
                    required_tool="DesktopAgent",
                    required_model="gemma3",
                    fallback_strategy="abort_workflow",
                    estimated_cost=0.0,
                    estimated_latency_ms=100.0,
                    estimated_risk=0.0
                )
            )
            subtasks.append(
                AtomicTask(
                    task_id="task_2",
                    description=f"Search online for: '{intent.primary_goal}'",
                    expected_output="raw_search_results",
                    required_tool="WebSearch",
                    required_model="gemini-2.0-flash",
                    fallback_strategy="fallback_to_local_search",
                    estimated_cost=0.005,
                    estimated_latency_ms=2500.0,
                    estimated_risk=0.3,
                    dependencies=["task_1"]
                )
            )
            subtasks.append(
                AtomicTask(
                    task_id="task_3",
                    description="Summarize findings from search results",
                    expected_output="search_summary",
                    required_tool=None,
                    required_model="gemini-2.0-flash",
                    fallback_strategy="use_raw_snippets",
                    estimated_cost=0.002,
                    estimated_latency_ms=1500.0,
                    estimated_risk=0.2,
                    dependencies=["task_2"]
                )
            )
            
            # Map secondary goal to file or notes save
            second_goal_desc = intent.secondary_goal or "save results"
            if any(w in second_goal_desc for w in ["note", "notes", "save note"]):
                subtasks.append(
                    AtomicTask(
                        task_id="task_4",
                        description=f"Save summarized findings to notes folder",
                        expected_output="note_save_confirmation",
                        required_tool="NotesManager",
                        required_model="gemma3",
                        fallback_strategy="abort_workflow",
                        estimated_cost=0.0,
                        estimated_latency_ms=800.0,
                        estimated_risk=0.2,
                        dependencies=["task_3"]
                    )
                )
            else:
                subtasks.append(
                    AtomicTask(
                        task_id="task_4",
                        description=f"Create file on system using search findings",
                        expected_output="file_save_confirmation",
                        required_tool="FileCreator",
                        required_model="gemma3",
                        fallback_strategy="abort_workflow",
                        estimated_cost=0.0,
                        estimated_latency_ms=1000.0,
                        estimated_risk=0.3,
                        dependencies=["task_3"]
                    )
                )

        return subtasks
