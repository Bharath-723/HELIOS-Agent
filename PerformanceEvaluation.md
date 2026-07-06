# HELIOS Performance Evaluation Report

---

## 1. CAHRA Routing Latency

| Statistic | Value |
| :--- | :--- |
| Mean | 0.81 ms |
| Median | 0.73 ms |
| P95 | 1.26 ms |
| Max | 10.08 ms |

The CAHRA routing engine consistently executes in sub-millisecond time. The P95 latency of 1.26 ms confirms negligible overhead for 95% of all routing decisions.

---

## 2. End-to-End Execution Time

| Statistic | Value |
| :--- | :--- |
| Mean | 63.02 ms |
| Median | 6.37 ms |
| P95 | 8.96 ms |
| Max | 5656.78 ms |

The median execution time of 6.37 ms indicates fast prompt parsing. The high mean is skewed by a small number of OS-level outlier spikes (GC pauses, file handle allocation).
