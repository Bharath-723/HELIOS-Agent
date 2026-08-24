# HELIOS v2: Plan Optimizer Specification

This document specifies the design for the **Plan Optimization Engine** of HELIOS v2.

---

## 1. Role in the Reasoning Pipeline
The `PlanOptimizer` executes after strategy selection and before validation. Instead of completing planning with a static strategy selection, the optimizer iteratively transforms the plan structure to maximize execution utility before agent sign-off.

---

## 2. Iteration Loop Logic
The optimizer runs a convergence loop loaded from `optimization_rules.json`:
- **Analyzer Pass**: Runs `PlanAnalyzer` to spot bottlenecks (redundancies, duplicate tasks, sequential levels).
- **Transformation Pass**: Applies the refiner (`DependencyOptimizer`, `ParallelOptimizer`, `ResourceOptimizer`) to produce a candidate graph.
- **Evaluation**: Calculates the utility difference ($\Delta = U_{new} - U_{old}$).
- **Rollback Policy**: If $\Delta < 0$, the optimizer rolls back to the previous iteration's graph, reducing optimization confidence.
- **Loop Prevention**: Fingerprints are calculated for each iteration. If a duplicate fingerprint is found, the optimizer stops to prevent infinite loops.
