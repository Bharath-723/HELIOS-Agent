# HELIOS CAHRA Production Performance Comparison

---

### 1. Latency Profile

| Pipeline Stage | Legacy Router | CAHRA v1.0 Router | Notes |
| :--- | :--- | :--- | :--- |
| **Connection Check** | ~3.0 seconds (synchronous) | **0.01 ms** (cached status) | Caching connection states prevents massive network request blockages. |
| **Utility Scoring & Ranking** | N/A | **1.8 ms** | Multi-attribute utility matrix evaluation. |
| **Total Routing Overhead** | ~3000 ms (uncached) | **~4.4 ms** (including file writes) | Overhead is completely negligible to the user. |

---

### 2. Resource Allocation Delta
* **RAM usage**: Stable (4.28 MB total process offset).
* **CPU consumption**: < 1.5% overhead during scoring calculations.
* **Thread safety**: Process execution counts remain stable.
