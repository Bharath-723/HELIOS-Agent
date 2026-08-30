# HELIOS v2: Dependency Optimizer Specification

This document details the transitive dependency pruning logic implemented in HELIOS v2.

---

## 1. Goal
Execution plans can accumulate redundant sequential dependencies during task decomposition. The `DependencyOptimizer` prunes redundant edges to simplify the DAG structure and allow concurrent execution.

---

## 2. Path Search & Redundancy Check
A dependency edge $(t, \text{dep})$ is redundant if task $t$ can reach $\text{dep}$ via an alternative path through some other direct dependency:
- For each dependency $\text{dep}$ of task $t$:
  - Iterate over all other direct dependencies $d$ of task $t$.
  - Run a recursive depth-first path search: `has_path(d, dep)`.
  - If a path exists from $d$ to $\text{dep}$, then the direct dependency $(t, \text{dep})$ is redundant and pruned.

*Example*:
If $A \to B \to C$ (where $C$ depends on $B$ and $B$ depends on $A$) and a direct edge $C \to A$ exists:
- The path search finds that $C \to B \to A$ is a valid path.
- The direct edge $C \to A$ is redundant and pruned. Task $C$ only retains its dependency on $B$.
