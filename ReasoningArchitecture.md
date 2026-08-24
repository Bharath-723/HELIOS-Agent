# HELIOS v2: Reasoning Architecture

This document specifies the architectural blueprint for the **Cognitive Reasoning Plane** of HELIOS v2.

---

## 1. Architectural Model
HELIOS v2 introduces an isolated cognitive layer that decouples intent understanding and task planning from execution and routing. Under the new pipeline, the system thinks before acting:

```
[User Input] 
      │
      ▼
[Intent Understanding] ──► Extracts goals, constraints, categories
      │
      ▼
[Task Planner] ──► Decomposes goals into a series of Atomic Tasks
      │
      ▼
[Context Builder] ──► Gathers CPU, VRAM, internet, and privacy states
      │
      ▼
[Execution Planner] ──► Optimizes task assignments, latency, cost, and risk
      │
      ▼
[Execution Graph] ──► Validates DAG and generates topological order (Kahn's)
      │
      ▼
[Planning Logger] ──► Emits event traces
```

---

## 2. Core Architectural Design Decisions
1. **Immutable Strategy Representation**: The planning engine generates a fully resolved `ExecutionPlan` detailing step dependencies, tools, and models without performing any state changes or execution.
2. **Topological Ordering**: The execution sequence is structured as a Directed Acyclic Graph (DAG) using Kahn's algorithm, allowing parallel execution groups.
3. **Decoupled Adaptation Layer**: The planner uses `planning_rules.json` to assign base parameters, which are then dynamically optimized based on real-time hardware status and availability.
4. **Complete Isolation**: The entire planning engine runs inside `core/reasoning/` without modifying any legacy code from HELIOS v1.1, preserving the frozen research baseline.
