# HELIOS v2: Execution Graph (DAG Specification)

This document specifies the DAG construction, validation, and topological sorting algorithms implemented in HELIOS v2.

---

## 1. DAG Construction & Kahn's Algorithm
The `ExecutionGraphBuilder` validates that the set of subtasks is a Directed Acyclic Graph (DAG) using **Kahn's Algorithm**:
1. Compute in-degree counts for every node.
2. Initialize a queue with nodes of in-degree = 0.
3. Remove node $u$ from the queue, append to `execution_order`.
4. Decrement in-degree of all neighbors of $u$. If any neighbor reaches in-degree = 0, add to queue.
5. If the size of `execution_order` does not equal the task list length, a circular dependency exists (raises `ValueError`).

---

## 2. Parallel Execution Groups
Tasks with no mutual dependencies can run concurrently. The builder computes parallel levels:
- Each task's level is defined as $1 + \max(\text{levels of its dependencies})$, with baseline nodes at level 0.
- Tasks are grouped into lists corresponding to their levels, ensuring deterministic scheduling:
  - **Level 0**: Connectivity checks, input parameter parsing (independent).
  - **Level 1**: File search, web search execution.
  - **Level 2**: LLM Summarization.
  - **Level 3**: Notes saving, file writing.
- This mapping allows future agent runtimes to execute independent groups concurrently.
