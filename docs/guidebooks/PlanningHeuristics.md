# HELIOS v2: Planning Heuristics Specification

This document details the configurable heuristics parameters defined in `planning_heuristics.json`.

---

## 1. Local vs Cloud Locality
- Local model assignments receive a `1.0` multiplier, rewarding privacy and offloading cloud costs.
- Cloud model assignments receive a `0.5` multiplier, penalizing cost efficiency.

---

## 2. Concurrency Scoring
- The heuristics engine scores parallel efficiency by checking parallel levels against:
  - `maximum_efficiency_level`: Target depth of DAG.
  - `optimal_tasks_per_level`: Target tasks per group.
- Concurrent task levels receive high efficiency scores (up to `1.0`), while single-task levels receive a sequential penalty (`0.2`).

---

## 3. Cost Multipliers
- Local task costs evaluate to `0.0`.
- Cloud task costs are computed using `cloud_api_cost_per_token` to project token expenses.
- These configurations ensure that local execution strategies are preferred when costs are prioritized.
