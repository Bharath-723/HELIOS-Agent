# HELIOS v2: Planning Trace Specification

This document specifies the structure and stages recorded inside the `PlanningTrace` in HELIOS v2.

---

## 1. Stage-Preserving Design
To assist research diagnostics and verification modules, the trace captures the inputs and outputs of every stage:
1. **planning_memory_check**: Records whether the cache has a matching graph.
2. **strategy_generation**: Records all candidate strategy names generated.
3. **constraint_filtering**: Records candidates remaining after applying severities.
4. **strategy_evaluation**: Records raw utility scores for each valid strategy.
5. **strategy_ranking**: Records the sorted order of candidate names.
6. **strategy_selection**: Records the final optimal choice and its confidence.

---

## 2. Telemetry and Logging
The trace records:
- `all_strategies`: Complete list of candidates generated.
- `filtered_strategies`: Valid candidates.
- `ranked_strategies`: Map of strategy name to utility score.
- `selected_strategy_name`: Win candidate.
- `decision_rationale`: Summarized text.
- `planning_duration_ms`: Duration of the planning execution.
This information is exported in structured JSON via `PlanningLogger`.
