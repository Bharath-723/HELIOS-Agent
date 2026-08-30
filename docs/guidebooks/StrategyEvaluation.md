# HELIOS v2: Strategy Evaluation Specification

This document details the evaluation scoring and metrics computed for each candidate plan strategy in HELIOS v2.

---

## 1. Metrics Evaluated
For every generated strategy, the `StrategyEvaluator` computes:
- **Total Cost**: Total estimated cloud API costs.
- **Estimated Latency**: Max latency per parallel level summed sequentially.
- **Complexity**: Extracted from the intent complexity score.
- **Parallel Efficiency**: Scoring concurrency gains vs sequential execution.
- **Failure Probability**: Max risk value among individual tasks.
- **Privacy Score**: Proportion of tasks allocated to local models.
- **Tool Utilization**: Percentage of steps using deterministic tools.

---

## 2. Metric Normalization
To compute a fair score, raw metrics are mapped to a standardized $[0, 1]$ interval:
- Cost: $\text{norm\_cost} = \frac{1.0}{1.0 + \text{cost} \times 100.0}$
- Latency: $\text{norm\_latency} = \frac{1.0}{1.0 + \frac{\text{latency}}{1000.0}}$
- Failure Probability: $\text{norm\_fail} = 1.0 - \text{failure\_prob}$
- Complexity: $\text{norm\_complexity} = 1.0 - \text{complexity}$
Values close to $1.0$ indicate optimal performance.
