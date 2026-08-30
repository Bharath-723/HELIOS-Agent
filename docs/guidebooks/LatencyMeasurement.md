# HELIOS Latency Measurement Specification

---

### 1. Timing Precision
* **Mechanism**: Utilizes `time.perf_counter()` to obtain fractional second timings.
* **Accuracy**: Sub-microsecond accuracy levels on Windows platforms.
* **Target Stages**:
  * Feature Extraction
  * Constraint evaluation
  * Scores math
  * Ranking execution
  * Total E2E parser.
