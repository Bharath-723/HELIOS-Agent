# HELIOS v2: Execution Graph Builder Specification

This document details the separation of graph representation from graph compilation in HELIOS v2.

---

## 1. Decoupled Design
In HELIOS v2, the `ExecutionGraph` is a pure, immutable data structure, while the `ExecutionGraphBuilder` contains all the topological sort and scheduling logic:
- **ExecutionGraph (Models)**: Stores tasks, execution order, parallel groups, fallbacks, and retry policies.
- **ExecutionGraphBuilder (Builder)**: Resolves adjacency lists, executes Kahn's algorithm, builds concurrent execution levels, and attaches retry/fallback logic.

---

## 2. Scheduling Levels
The builder maps tasks to parallel groups so that independent tasks execute concurrently:
- **Level 0**: Independent setup, connectivity verification, parsing.
- **Level 1**: API retrieval, file parsing, web search execution.
- **Level 2**: Synthesis and summarization.
- **Level 3**: note writing, email sending, filesystem actions.

This level mapping enables future execution engines to schedule parallel processes safely.
