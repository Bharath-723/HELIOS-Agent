# HELIOS v2: Retrieval Planning Specification

This document details the retrieval planning heuristics implemented in HELIOS v2.

---

## 1. Goal
When given an `ExecutionPlan`, the `RetrievalPlanner` parses subtask dependencies to determine what information needs to be retrieved before execution.

---

## 2. Resource Constraints & Cost Analysis
- The planner assigns retrieval targets to specific memory layers:
  - Tasks using `WebSearch` -> L4 Knowledge Search + Web Query tasks.
  - Tasks using `NotesManager` -> L3 Persistent Memory scans.
  - Default tasks -> L1/L2 Memory searches.
- Projected retrieval latencies and costs are aggregated from weights specified in `knowledge_rules.json`.
- Compiles a unified `RetrievalPlan` detailing retrieval steps, priorities, and cost metrics.
