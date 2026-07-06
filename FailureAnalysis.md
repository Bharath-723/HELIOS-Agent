# HELIOS Failure Analysis Report

---

## 1. Failure Summary

| Metric | Value |
| :--- | :--- |
| Total Failures (task_success=0) | 780 / 900 |
| Overall Failure Rate | 86.67% |

---

## 2. Root Cause

The dominant failure mode is **routing mismatch**: the ground-truth expected LOCAL routing for 780 of the 900 executions, but the CAHRA constraint engine force-routed all prompts to CLOUD because the local Ollama server was unavailable during the benchmark session.

This is **not an algorithm defect**. The constraint `check_local_model` correctly detected that no local model was running and applied the fallback policy.

---

## 3. Intent Parsing Failures

| Category | Intent Accuracy | Failure Cause |
| :--- | :--- | :--- |
| system_controls | 50.00% | Ambiguous prompts: "set volume to X%" parsed as `volume_up` regardless of direction |
| All other categories | 100.00% | No intent parsing failures |

---

## 4. Failure Distribution by Category

All 13 categories with `expected_route=LOCAL` produced 0% task success because of the cloud-only constraint override. The 2 categories with `expected_route=CLOUD` (`web_search`, `mixed_workflow`) achieved 100% task success.
