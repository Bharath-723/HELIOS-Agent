# HELIOS Resource Monitoring Specification

---

### 1. Monitoring Flow
The resource monitor queries properties from the active OS process handles:

* **Trigger**: Invoked at the completion of every routed benchmark prompt.
* **Mechanism**: Calls `psutil.Process(os.getpid()).memory_info().rss` and `psutil.cpu_percent()`.
* **Uptime Safety**: Failsafe try-except statements catch any permission or OS compatibility anomalies, defaulting to zero.
