# HELIOS Benchmark Framework Report

---

### 1. Framework Summary
The HELIOS Benchmark Execution Framework provides an automated pipeline to run the 300 frozen prompts against the production integrated `HELIOSAgent` and analyze results against ground-truth labels.

* **Immunity**: The dataset remains completely immutable.
* **Execution flow**: Programmatically invokes `NLRouter` and gathers routing traces from `data/diagnostics/`.
