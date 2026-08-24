# HELIOS v2: Adaptive Planning Specification

This document specifies the architectural design for the **Adaptive Cognitive Planning Engine** of HELIOS v2.

---

## 1. Process Lifecycle
HELIOS v2 transitions from static task decomposition to a dynamic, multi-strategy candidate selection lifecycle:

```
[User Input] ──► Parse Intent ──► Task Understanding ──► Complexity Estimation
                                                                  │
[Context] ────────────────────────────────────────────────────────┼──► Generate Candidates
                                                                  │      (Policies)
[Planning Memory Cache] ◄──(Structure Reused)───(Match Key)───────┤
                                                                  ▼
Selected Graph ◄── Validate ◄── Explain ◄── Select ◄── Rank ◄── Filter Constraints
```

---

## 2. Dynamic Planning Memory Cache
The engine utilizes a `PlanningMemory` structure to cache previously optimized DAG topologies.
- **Cache Indexing**: Keys are compiled from `TaskIntent` parameters and `ReasoningContext` configurations (such as network and local model presence).
- **Environment Safety**: If the runtime environment changes (e.g. system transitions from online to offline), cache generation produces a miss, forcing recalculation of valid strategies.
