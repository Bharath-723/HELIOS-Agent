# HELIOS v2: Plan Refiner Specification

This document details the plan refinement process and Plan Equivalence Verification implemented in HELIOS v2.

---

## 1. Modular Refinement Pipeline
The `PlanRefiner` coordinates the application of sub-optimizers:
1. **Dependency Optimizer**: Prunes redundant transitive relationships.
2. **Parallel Optimizer**: Maximizes concurrent execution layers by removing artificial sequential dependencies.
3. **Resource Optimizer**: Substitutes local models and optimizes tool execution schedules to prevent loading/unloading overhead.

---

## 2. Plan Equivalence Verification
Before committing any transformation, the refiner asserts that the modified plan is semantically equivalent to the original plan:
- **Task Confinement Check**: Asserts that no vital task is dropped. Only helper tasks explicitly flagged as redundant (e.g. redundant connectivity checks) can be pruned.
- **Output Preservation**: Verifies that expected output schemas and types remain unchanged for each subtask.
- **Dependency Soundness**: Builds the refined tasks sequence via the graph builder to assert that no circular cycles are introduced.

If any check fails, the refinement is rejected, and the refiner returns the original unrefined graph.
