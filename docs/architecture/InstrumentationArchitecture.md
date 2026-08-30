# HELIOS Instrumentation Architecture

---

### 1. Architectural Structure
The metrics gathering system decouples latency, resource consumption, and routing statistics:

```
benchmark/metrics/
  ├── resource_monitor.py      # Captures system CPU/RAM/threads
  ├── latency_profiler.py      # Measures millisecond duration offsets
  ├── routing_statistics.py    # Gathers selection counts and margins
  ├── execution_statistics.py  # Computes success/failure ratios
  └── metrics_collector.py     # Unified orchestrator & file writer
```
