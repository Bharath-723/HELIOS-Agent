# HELIOS v2: Plan Optimization Metrics

This document details the metrics computed by `OptimizationMetricsCalculator` to evaluate refinement passes in HELIOS v2.

---

## 1. Metric Mappings
- **Cost Savings**: Computes projected cost reduction:
  
  $$\text{Savings} = \text{Cost}_{\text{baseline}} - \text{Cost}_{\text{optimized}}$$
  
- **Latency Reduction**: Measures sequential latency reductions in milliseconds:
  
  $$\text{Reduction} = \text{Latency}_{\text{baseline}} - \text{Latency}_{\text{optimized}}$$
  
- **Dependency Reduction**: Measures number of pruned dependencies.
- **Parallelism Increase**: Calculates the increase in average tasks per parallel group:
  
  $$\Delta P = \frac{N_{\text{tasks\_opt}}}{D_{\text{groups\_opt}}} - \frac{N_{\text{tasks\_base}}}{D_{\text{groups\_base}}}$$
  
- **Utility Improvement**: Measures raw score change.

---

## 2. Optimization Gain
The overall optimization gain is computed directly from the utility improvement score. If no improvements are found, the gain defaults to `0.0`. These metrics are compiled into `PlanOptimizationMetrics` and attached to the `ExecutionPlan` trace.
