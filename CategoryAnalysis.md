# HELIOS Category Analysis Report

---

## Per-Category Benchmark Results

| Category | Count | Intent Acc | Route Acc | Success Rate | Avg Exec (ms) | Avg Route (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| file_management | 60 | 100.00% | 0.00% | 0.00% | 162.55 | 0.93 |
| notes | 60 | 100.00% | 0.00% | 0.00% | 6.86 | 0.84 |
| scheduling | 60 | 100.00% | 0.00% | 0.00% | 6.37 | 0.77 |
| desktop_automation | 60 | 100.00% | 0.00% | 0.00% | 154.48 | 0.75 |
| system_controls | 60 | 50.00% | 0.00% | 0.00% | 81.52 | 0.80 |
| application_control | 60 | 100.00% | 0.00% | 0.00% | 6.78 | 0.81 |
| document_processing | 60 | 100.00% | 0.00% | 0.00% | 6.56 | 0.80 |
| **web_search** | **60** | **100.00%** | **100.00%** | **100.00%** | **174.36** | **0.77** |
| general_conversation | 60 | 100.00% | 0.00% | 0.00% | 82.91 | 0.79 |
| hardware_queries | 60 | 100.00% | 0.00% | 0.00% | 5.84 | 0.64 |
| privacy_sensitive | 60 | 100.00% | 0.00% | 0.00% | 6.34 | 0.80 |
| multi_step | 60 | 100.00% | 0.00% | 0.00% | 80.49 | 0.85 |
| **mixed_workflow** | **60** | **100.00%** | **100.00%** | **100.00%** | **156.82** | **1.05** |
| failure_recovery | 60 | 100.00% | 0.00% | 0.00% | 7.17 | 0.80 |
| system_information | 60 | 100.00% | 0.00% | 0.00% | 6.26 | 0.78 |

> [!NOTE]
> Categories `web_search` and `mixed_workflow` are the only two categories that expected CLOUD routing. Since CAHRA routed everything to CLOUD (due to offline Ollama), these two categories achieved 100% route match while all LOCAL-expected categories scored 0% route match.

> [!NOTE]
> The `system_controls` category achieved only 50% intent accuracy because half of the prompts expected `volume_down` while the LLM consistently parsed them as `volume_up` (the prompts phrased as "set volume to X percent" are ambiguous regarding direction).
