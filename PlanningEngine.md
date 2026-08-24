# HELIOS v2: Planning Engine Specification

This document details the responsibilities and behaviors of the `IntentUnderstandingEngine` and the `TaskPlanner` in HELIOS v2.

---

## 1. Intent Understanding Engine
The `IntentUnderstandingEngine` parses raw user prompts to extract critical semantic metadata:
- **Primary / Secondary Goal**: Identifies multiple steps (e.g., split on `"and summarize to"`).
- **Task Category**: Resolves to `TaskCategory` (CHAT, FILE, NOTES, SCHEDULE, SEARCH, PRIVACY_TASK, or MIXED) using pattern matching based on `planning_rules.json`.
- **Requirements**:
  - **Privacy**: High (sensitive indicators), Medium (local file/notes access), or Low.
  - **Internet**: True if prompt matches freshness indicators or explicitly requests web/browser searches.
- **Expected Output**: Structured file, text, or scheduler confirmation.
- **Complexity and Urgency**: Scored from 0.0 to 1.0 to inform capability adjustments.

---

## 2. Task Planner
The `TaskPlanner` translates the parsed intent into a linear or branched series of `AtomicTask` steps:
- **Subtask Decomposition**: Maps categories to atomic steps.
  - *Example*: A mixed search-and-save prompt maps to:
    1. Connectivity check
    2. Search execution
    3. LLM Summarization
    4. NotesManager note saving
- **Subtask Dependencies**: Links dependent tasks by matching outputs (e.g., summarization depends on search results).
- **Subtask Fallbacks**: Registers fallback actions (e.g., `fallback_to_cloud` or `abort_workflow`) for each task.
