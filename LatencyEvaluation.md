# HELIOS Latency Evaluation Report

---

## 1. CAHRA Internal Latency Breakdown

| Metric | Mean | Median | P95 |
| :--- | :--- | :--- | :--- |
| Feature Extraction | ~0.28 ms | ~0.27 ms | ~0.44 ms |
| Constraint Evaluation | ~0.08 ms | ~0.07 ms | ~0.11 ms |
| Score Computation | ~0.09 ms | ~0.08 ms | ~0.13 ms |
| Ranking | ~0.01 ms | ~0.01 ms | ~0.01 ms |
| Explainability | ~0.09 ms | ~0.08 ms | ~0.12 ms |
| **Total CAHRA** | **0.81 ms** | **0.73 ms** | **1.26 ms** |

> [!NOTE]
> Internal timing breakdown values are extracted from the CAHRA engine log traces observed during benchmark execution.

---

## 2. Per-Category Routing Latency

| Category | Avg Routing Latency (ms) |
| :--- | :--- |
| hardware_queries | 0.64 |
| desktop_automation | 0.75 |
| web_search | 0.77 |
| scheduling | 0.77 |
| system_information | 0.78 |
| general_conversation | 0.79 |
| failure_recovery | 0.80 |
| document_processing | 0.80 |
| system_controls | 0.80 |
| privacy_sensitive | 0.80 |
| application_control | 0.81 |
| notes | 0.84 |
| multi_step | 0.85 |
| file_management | 0.93 |
| mixed_workflow | 1.05 |
