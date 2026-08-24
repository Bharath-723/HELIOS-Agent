# HELIOS v2: Reasoning Models

This document lists the dataclasses and field types defined in `core/reasoning/reasoning_models.py`.

---

## 1. TaskIntent (Frozen Dataclass)
- `primary_goal`: `str` (First/main action extracted)
- `secondary_goal`: `Optional[str]` (Carry-forward action)
- `category`: `TaskCategory` (CHAT, FILE, NOTES, SCHEDULE, SEARCH, PRIVACY_TASK, MIXED)
- `privacy_requirement`: `str` ("high", "medium", "low")
- `requires_internet`: `bool`
- `requires_tools`: `List[str]`
- `expected_output`: `str`
- `complexity_score`: `float`
- `urgency_level`: `str`
- `dependencies`: `List[str]`

---

## 2. AtomicTask (Dataclass)
- `task_id`: `str` (e.g. `"task_1"`)
- `description`: `str`
- `expected_output`: `str`
- `required_tool`: `Optional[str]` (Tool class target)
- `required_model`: `str` (Candidate model recommendation)
- `fallback_strategy`: `str` (Adaptive execution behavior)
- `estimated_cost`: `float`
- `estimated_latency_ms`: `float`
- `estimated_risk`: `float` (0.0 to 1.0)
- `dependencies`: `List[str]`
- `state`: `TaskState` (PENDING, COMPLETED, FAILED, SKIPPED)
- `execution_result`: `Optional[str]`

---

## 3. ExecutionGraph (Frozen Dataclass)
- `tasks`: `Dict[str, AtomicTask]`
- `execution_order`: `List[str]` (Topological sorted list)
- `parallel_groups`: `List[List[str]]` (Concurrent execution layers)
- `fallback_nodes`: `Dict[str, str]`
- `retry_policies`: `Dict[str, int]`
- `verification_checks`: `List[str]`

---

## 4. ExecutionPlan (Frozen Dataclass)
- `plan_id`: `str`
- `prompt`: `str`
- `intent`: `TaskIntent`
- `context`: `ReasoningContext`
- `graph`: `ExecutionGraph`
- `planning_time_ms`: `float`
- `planning_confidence`: `float`
- `decision_path_summary`: `str`
- `created_at`: `str`
