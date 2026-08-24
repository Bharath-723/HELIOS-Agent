# HELIOS v2: Parallel Optimizer Specification

This document details the concurrency-maximization logic implemented in HELIOS v2.

---

## 1. Concurrency Bottlenecks
Linear planning chains often introduce artificial sequential locks. For example, a note-saving task depending directly on a network-connectivity task creates an artificial lock, forcing note drafting to wait until the network verification completes.

---

## 2. Dependency Disentanglement
The `ParallelOptimizer` inspects task specifications to prune artificial dependencies:
- **Rule**: If a dependency task represents a system check or metadata parse (such as connectivity verification) and the current task is a local resource operation (such as note saving or file creation) that does not directly require the checked resource:
  - Prune the dependency edge.
  - The local note/file operation is scheduled in parallel with the main network query, maximizing concurrent utilization.
- This allows independent branches of the DAG to execute simultaneously at Level 0 or Level 1.
