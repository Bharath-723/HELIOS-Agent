# HELIOS Primary Research Questions

---

### RQ1: Does CAHRA improve routing decisions compared to legacy rule-based routing?
* **Motivation**: Verify if capability-aware optimizations prevent sub-optimal local executions or unnecessary cloud calls.
* **Evaluation Metrics**: Routing Accuracy (RA).
* **Expected Evidence**: CAHRA routing accuracy above 95% compared to baseline string-match heuristics.

---

### RQ2: What is the latency overhead introduced by CAHRA?
* **Motivation**: Quantify decision processing time to ensure it does not negatively impact user experience.
* **Evaluation Metrics**: Routing Latency (RL).
* **Expected Evidence**: Average routing time below 5 ms.

---

### RQ3: How effectively does HELIOS preserve user privacy under CAHRA?
* **Motivation**: Verify that sensitive local queries containing credentials or private file contents are never routed to cloud providers.
* **Evaluation Metrics**: Local Execution Rate (LER) for sensitive inputs.
* **Expected Evidence**: 100% of privacy-sensitive prompts containing credentials route locally or trigger local-forcing constraints.
