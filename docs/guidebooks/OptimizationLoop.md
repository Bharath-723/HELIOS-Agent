# HELIOS v2: Optimization Loop & Rollback Specification

This document specifies the convergence loop and rollback policies implemented in the `PlanOptimizer` of HELIOS v2.

---

## 1. Convergence Loop Architecture
The optimization loop runs iteratively up to `max_iterations = 5`:

```
[Baseline Plan] ──► Analyze ──► Refine ──► Evaluate Utility
                                               │
               ┌───────────────────────────────┴──────────────────────────────┐
               ▼ (Diff < 0)                                                    ▼ (Diff >= Convergence Threshold)
        [Trigger Rollback]                                             [Commit Optimization State]
               │                                                               │
               ├──► Restore previous graph                                     ├──► Store fingerprint
               └──► Stop loop                                                  └──► Proceed to next iteration
```

---

## 2. Rollback Policy
If a transformation reduces utility, the optimizer triggers an automatic rollback:
- Restores the graph to the previous iteration's state.
- Decreases optimization confidence by 20% to warn downstream modules.
- Immediately halts the loop.

---

## 3. Fingerprint Loop Prevention
- The optimizer computes a deterministic hash fingerprint of the graph at each iteration.
- If the fingerprint of a refined graph matches a previously seen fingerprint, a loop is detected. The optimizer stops to prevent infinite loops.
