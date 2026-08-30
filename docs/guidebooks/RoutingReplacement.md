# HELIOS Routing Replacement Report

---

### 1. Old Routing Pathway (Legacy)
* **Logic**: Simple string keyword scan (`ONLINE_TRIGGERS` like `"latest news"`, `"weather in"`) in `llm_engine.py`.
* **Selection**: Strict binary choice (Local vs Cloud).
* **Limitations**: Fails to react to hardware changes (low RAM, GPU availability) or differentiate model capability classes.

---

### 2. New Routing Pathway (CAHRA v1.0)
* **Logic**: pipe query context through the multi-attribute utility calculation comparing task requirements to model capabilities.
* **Selection**: Model-specific candidate ranking (`gemma3`, `mistral`, `gemini-2.0-flash`, `gpt-4`).
* **Attributes evaluated**: Privacy, freshness, complexity, cost, latency.

---

### 3. Fallback Pathways
* If any error or exception occurs in the CAHRA package, the router logs a trace and invokes the legacy `llm.chat(prompt, system=SYSTEM)` method, ensuring continuous execution.
