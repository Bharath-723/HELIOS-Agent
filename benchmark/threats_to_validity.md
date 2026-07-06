# Threats to Validity

---

### 1. Internal Validity
* **Threat**: Uncontrolled OS background processes causing CPU/RAM metrics to fluctuate, impacting dynamic capability adjustments.
* **Mitigation**: Average measurements over multiple warm-up repetitions and log background CPU thresholds before running benchmark queries.

---

### 2. External Validity
* **Threat**: Hardcoded keyword heuristics in `routing_rules.json` may fail to generalize to novel user prompts or colloquial phrasing.
* **Mitigation**: Evaluate a diverse test set containing varied paraphrasing and grammatical complexity.

---

### 3. Construct Validity
* **Threat**: Mismatch calculations $|Requirement - Capability|$ might not perfectly capture execution success rates.
* **Mitigation**: Correlate routing scores with actual final task completion rates across all candidate models.
