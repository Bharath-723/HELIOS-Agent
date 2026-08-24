# HELIOS v2: Task Understanding Specification

This document details the responsibilities and behaviors of the `TaskUnderstandingEngine` in HELIOS v2.

---

## 1. Role in the Reasoning Pipeline
The `TaskUnderstandingEngine` bridges the semantic gap between high-level intent parsing (`TaskIntent`) and task decomposition (`TaskPlanner`).
- **TaskIntent** answers: *"What does the user want?"* (Primary goal, category, constraints).
- **TaskUnderstanding** answers: *"What work must actually be performed?"* (Implicit tasks, inferred dependencies, output expectations, resource profiles).

---

## 2. Inferred Tasks and Dependencies
The engine analyzes constraints and category settings to extract implicit actions:
- **Search Category**: Infers network availability checking, raw web queries, and evidence synthesis, setting dependencies sequentially.
- **Privacy Category**: Infers data sanitization/redaction steps, offline local model selection, and local file storage confinement.
- **Mixed Category**: Deconstructs compound prompts into multi-agent DAG dependencies (e.g. search -> download -> parse -> write).

---

## 3. Execution Constraints
It formalizes execution constraints like:
- `must_execute_on_local_model`
- `requires_active_connectivity`
- `data_confinement_active`
- `optimize_for_minimum_latency`
These constraints are evaluated during execution mapping in the task planner.
