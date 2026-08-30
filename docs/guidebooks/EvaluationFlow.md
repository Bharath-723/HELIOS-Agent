# HELIOS Evaluation Flow Specification

---

### 1. Evaluation Flow Sequence
Results are processed using the following sequence:

```
Observed Intent/Route + Ground Truth -> GroundTruthEvaluator -> Match Verdicts -> Statistics Compiler -> Report MD
```

* **Matches**: Evaluates parsed params, model selections, and CPU/RAM offsets.
* **Aggregations**: Summarizes precision ratios per category and difficulty.
