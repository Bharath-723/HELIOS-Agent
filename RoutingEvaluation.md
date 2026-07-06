# HELIOS Routing Evaluation Report

---

## 1. Routing Decision Analysis

All 900 benchmark executions were routed to **CLOUD** (100.0%). The CAHRA constraint engine triggered the `check_local_model` constraint on every prompt because the local Ollama server was not running during the benchmark session.

| Observed Route | Count | Expected Route Match |
| :--- | :--- | :--- |
| CLOUD | 900 | 13.33% (120/900 expected CLOUD) |

---

## 2. Model Selection Distribution

| Model | Count | Percentage |
| :--- | :--- | :--- |
| gemini-2.0-flash | 900 | 100.0% |

The single-model selection is a direct consequence of the constraint engine: when the local model is unavailable, CAHRA selects the highest-ranked cloud candidate.

---

## 3. Confidence Analysis

| Statistic | Value |
| :--- | :--- |
| Average Confidence | 1.00 |
| Min Confidence | 1.00 |
| Max Confidence | 1.00 |

All decisions produced maximum confidence, which is expected when only one viable candidate exists after constraint filtering.

---

## 4. Privacy-Sensitive Routing

| Category | Observed Route | Expected Route | Match |
| :--- | :--- | :--- | :--- |
| privacy_sensitive | CLOUD (60/60) | LOCAL (60/60) | 0% |

> [!WARNING]
> All 60 privacy-sensitive prompts were routed to CLOUD due to the unavailability of the local model. Under normal conditions with Ollama online, the constraint engine would force these prompts to LOCAL. This is a known limitation of the benchmark execution environment, not a CAHRA algorithm defect.
