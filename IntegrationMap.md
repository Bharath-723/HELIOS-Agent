# HELIOS CAHRA Production Integration Map

---

### 1. Points of Entry
* **Component**: `NLRouter` in `core/nl_router.py`
* **Method**: `parse(self, user_input: str, context: str = "")`
* **Trigger**: Every user message processed by `HELIOSAgent` routes through `NLRouter.parse`.

---

### 2. Context Extraction Flow
On invocation of `parse()`:
1. Dynamic retrieval of system metrics:
   * **RAM**: `psutil.virtual_memory().available` (in MB)
   * **CPU**: `psutil.cpu_percent()`
2. Dynamic status of models and connection services:
   * **Internet**: `self.llm._internet_ok()`
   * **Local model service**: `self.llm._ollama_alive()`
   * **Cloud provider**: `self.llm._has_any_cloud_key()`
3. Initialize `RoutingContext` containing prompt, intent, and hardware variables.

---

### 3. Model Override Flow
* Retrieve `RoutingResult` from `RoutingEngine.route(context)`.
* Best candidate model (`res.selected_model`) overrides `self.llm` configs temporarily using a `try-finally` context:
  * For `CLOUD` decision: Sets `self.llm.mode = "online"` and adjusts `self.llm.gemini_model` or `self.llm.openai_model`.
  * For `LOCAL` decision: Sets `self.llm.mode = "offline"` and adjusts `self.llm.ollama_model`.
* Execute request via `self.llm.chat(prompt, system=SYSTEM)`.
* Revert configurations to original states.
