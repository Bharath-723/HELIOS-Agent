# HELIOS Difficulty Analysis Report

---

## Per-Difficulty Benchmark Results

| Difficulty | Count | Intent Acc | Route Acc | Success Rate | Avg Exec (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Easy | 294 | 96.94% | 14.29% | 14.29% | 97.36 |
| Medium | 294 | 95.92% | 14.29% | 14.29% | 21.99 |
| Hard | 252 | 96.43% | 14.29% | 14.29% | 66.66 |
| Multi-Step | 60 | 100.00% | 0.00% | 0.00% | 80.49 |

> [!NOTE]
> Intent accuracy is stable across all difficulty levels (95.9%–100%), indicating that prompt parsing quality does not degrade with increased complexity. The routing accuracy of 14.29% for Easy/Medium/Hard corresponds to the `web_search` and `mixed_workflow` prompts within those difficulties — the only prompts that expected CLOUD routing.
