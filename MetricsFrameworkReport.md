# HELIOS Metrics Instrumentation Report

---

### 1. Framework Summary
The Metrics Collection & Instrumentation Framework provides the foundation for gathering latency, CPU/RAM resource footprint, thread activity, and routing accuracy.

* **Overhead**: Instrumentation runs natively via `psutil` handles, preserving < 0.1% CPU consumption.
* **Storage**: Data is exported dynamically to CSV and JSON formats under `benchmark/metrics/`.
