# HELIOS End-to-End Routing Trace Report

---

### 1. End-to-End Routing Path Trace
We verified the complete execution path for the prompt: *"Create a note for tomorrow"*

1. **User Prompt**: *"Create a note for tomorrow"*
2. **Intent Parser**: Evaluates syntax via `NLRouter.parse()`.
3. **RoutingContext**:
   * CPU/RAM: Checked dynamically.
   * Connectivity: Cached checks (`True`/`False`).
4. **Feature Extraction**: Scans keywords. Privacy requirement = 0.70, freshness = 0.00.
5. **Constraints check**: Triggers `check_local_model` (due to Ollama server status being offline). Force CLOUD.
6. **Candidate Ranking**: Evaluates cloud models (`gemini-2.0-flash`, `gpt-4`).
7. **Selected Model**: `gemini-2.0-flash` (highest satisfaction score).
8. **Inference Execution**: Router temporarily overrides active model configs, fires `self.llm.chat()`, and receives intent JSON.
9. **Diagnostics**: Saves trace snapshot to disk (`data/diagnostics/decision_snapshot.json`).
