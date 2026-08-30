# HELIOS v2: Planning Validator Specification

This document details the checks and rules implemented in the `PlanningValidator` of HELIOS v2.

---

## 1. Goal
The validator acts as a gatekeeper in the cognitive planning pipeline. Every compiled `ExecutionPlan` must pass the validator before it is signed off for agent execution.

---

## 2. Validation Test Suite Checks

### 2.1 Graph & Topological Safety
- **Circular Dependencies**: Traverses subtasks using Kahn's algorithm topological sorting. If any cycle is detected, validation fails immediately.
- **Missing Dependencies**: Asserts that every subtask listed in a dependency array actually exists in the task map.
- **Duplicate Task IDs**: Asserts that all task IDs in the plan are unique.

### 2.2 System & Model Feasibility
- **Tool Availability**: Confirms that all tools assigned to tasks (e.g. `NotesManager`, `TaskScheduler`) are registered in the current `ReasoningContext`'s available tools.
- **Model Availability**: Confirms that all recommended candidate models are supported by the environment.

### 2.3 Constraint Enforcement
- **Privacy Confinement**: If the intent requires high privacy, any task assigned to a Cloud model (e.g. Gemini, GPT) raises a validation error.
- **Empty Plans**: Empty task lists fail validation immediately.
- **Fallback Verification**: Generates warnings for unrecognized fallback strategies.
