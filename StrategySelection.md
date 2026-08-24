# HELIOS v2: Strategy Selection & Tie-Breaker Specification

This document details the selection logic, confidence margin, and tie-breaker policies implemented in HELIOS v2.

---

## 1. Optimal Selection & Explanations
The `StrategySelector` chooses the top-ranked strategy and compiles:
- **Advantages / Disadvantages**: Bulleted summaries explaining the operational features of the chosen strategy (privacy preservation, parallel efficiency, costs, risks).
- **Selection Explanation**: Natural-language rationale explaining why this plan won.
- **Rejected Explanations**: Maps each candidate strategy to its margin difference, justifying the rejection.

---

## 2. Selection Margin and Confidence
- **Selection Margin**: Computed as the absolute difference between the utility score of Rank 1 and Rank 2:
  
  $$\Delta = U(\text{Rank}_1) - U(\text{Rank}_2)$$
  
- **Selection Confidence**: Computed as the ratio of the margin to the optimal score:
  
  $$\text{Confidence} = \min\left(1.0, \max\left(0.1, \frac{|\Delta|}{|U(\text{Rank}_1)|}\right)\right)$$

---

## 3. Deterministic Tie-Breaker Policy
If two strategies achieve identical utility scores, the tie-breaker resolves priority deterministically:
1. **Lowest Cost**: The strategy with lower estimated cost comes first.
2. **Lowest Latency**: The strategy with lower estimated latency comes first.
3. **Lowest Failure Probability (Risk)**: The strategy with lower risk comes first.
4. **Alphabetical Name**: Sort alphabetically by strategy name.
This sequence guarantees identical selection results across executions.
