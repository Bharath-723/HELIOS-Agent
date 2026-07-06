# HELIOS Execution Pipeline Specification

---

### 1. Execution Path
The runner sequentially executes prompts using the following execution pipeline:

```
Dataset JSON -> Loader -> Prompts Queue -> Runner -> NLRouter/CAHRA -> Result Trace -> Outputs JSON
```

* **Controls**: Prompts execute in deterministic alphabetical or index order.
* **Warm-up**: Skips recording metrics for the first 5 prompts to warm caches.
* **Outputs**: Saves raw runs data into `data/benchmark_results/execution_result.json`.
