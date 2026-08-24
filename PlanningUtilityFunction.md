# HELIOS v2: Planning Utility Function Model

This document specifies the multi-objective utility formula used to rank alternative execution strategies.

---

## 1. Utility Formula
The utility of a planning strategy is computed using a weighted sum of normalized performance scores:

$$U(s) = \sum_{m \in M} w_m \cdot S_m(s)$$

Where:
- $M$ is the set of metrics: `{cost, latency, complexity, parallel_efficiency, failure_probability, privacy_score, tool_utilization, maintainability, recovery_capability}`.
- $S_m(s)$ is the normalized score of strategy $s$ for metric $m \in [0, 1]$.
- $w_m$ represents the weight coefficient loaded from `planning_weights.json`.

---

## 2. Utility Breakdown Reporting
Every evaluation output contains a detailed `utility_breakdown` dictionary:
- Shows the exact contribution ($w_m \cdot S_m(s)$) of each individual metric.
- *Example*:
  ```json
  "utility_breakdown": {
    "cost_contribution": -0.198,
    "latency_contribution": -0.041,
    "privacy_score_contribution": 0.200,
    "parallel_efficiency_contribution": 0.038
  }
  ```
This breakdown is exposed in planning trace telemetry to assist research evaluations and explainability modules.
