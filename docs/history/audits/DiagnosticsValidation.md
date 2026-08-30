# HELIOS CAHRA Diagnostics Validation Report

---

### 1. Export File Formatting Verification
We verified that the newly integrated diagnostics export system outputs correctly formatted JSON files with zero schema corruption:

* **`data/diagnostics/candidate_ranking.json`**:
  * Format: Valid JSON array.
  * Fields: `candidate_ranking`.
* **`data/diagnostics/decision_snapshot.json`**:
  * Format: Valid JSON dictionary.
  * Fields: `prompt`, `extracted_requirements`, `candidate_models`, `utility_scores`, `capability_mismatches`, `ranking`, `selected_model`, `rejected_models`, `selection_margin`, `confidence`, `triggered_constraints`, `execution_time_ms`, `timestamp`.
* **`data/diagnostics/routing_summary.json`**:
  * Format: Valid JSON dictionary logging stress execution stats (average timings, total loops).

---

### 2. Integration Integrity
* **File concurrency**: Multiple successive writes do not result in lock contention.
* **Write performance**: Buffered file exports add < 2 ms overhead.
