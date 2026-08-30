# HELIOS End-to-End Routing Trace Report

---

### 1. Representative Routing Trace
* **Prompt**: *"Create a note for tomorrow"*
* **Stage 1 (Intent Analysis)**: `NLRouter.parse()` triggered.
* **Stage 2 (Context Build)**: Dynamic memory, CPU, and cached connection statuses loaded into `RoutingContext`.
* **Stage 3 (CAHRA Run)**: Matches capabilities vs requirements. Triggers offline constraint (Ollama down). Force CLOUD.
* **Stage 4 (Candidate Selection)**: Ranks `gemini-2.0-flash` above `gpt-4` (due to lower cost and matching latency).
* **Stage 5 (Override Execution)**: Temporarily sets `self.llm` online settings, invokes Gemini, and receives `create_note` intent.
* **Stage 6 (Diagnostics)**: Saves decision trace snapshot to disk (`data/diagnostics/decision_snapshot.json`).
