# HELIOS Benchmark Framework Architecture

---

### 1. Architectural Structure
The framework is partitioned into four distinct modules to enforce separation of concerns:

```
benchmark/framework/
  ├── benchmark_loader.py       # Reads & validates JSON schemas
  ├── benchmark_runner.py       # Executes prompts on HELIOS agent
  ├── ground_truth_evaluator.py  # Calculates E2E match criteria (PASS/FAIL/PARTIAL)
  └── evaluation_engine.py      # Computes global statistics (accuracy ratios)
```
