# Bug Fix Report

This document records the exact changes made to HELIOS to resolve the 5 audited defects.

---

## Fix 1: Ollama Recovery & Retry Logic
- **File modified**: [llm_engine.py](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/llm_engine.py)
- **Change details**:
  - Imported the `logging` module to define `log` at the top of the file.
  - Replaced the simple request try-catch block inside `_call_local` with a robust retry loop.
  - Implemented exact-once retry with a 1-second delay for transient/server-side conditions: `ConnectionError`, `ConnectionResetError`, `Timeout`, `ReadTimeout`, and HTTP 5xx errors (500, 502, 503, 504).
  - Explicitly disabled retries for client-side errors like HTTP 4xx (e.g. 400 Bad Request, 401 Unauthorized), propagating detailed exceptions immediately.
  - Never suppresses exceptions; raises clear, detailed `RuntimeError` messages containing the HTTP status code and response body.

---

## Fix 2: Feature Extractor Rule Updates
- **File modified**: [routing_rules.json](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/routing/routing_rules.json)
- **Change details**:
  - Appended precise phrase-based keywords for web/browser searches under the `freshness` category: `"search google"`, `"search youtube"`, `"search online"`, `"search the web"`, `"web search"`, `"google search"`, `"youtube search"`, `"open website"`, `"open url"`.
  - Avoided single-word triggers like `"search"` under freshness to prevent false-positive matching on local queries like `"search my notes"` or `"search documents"`.

---

## Fix 3: Desktop Agent URL Redirection
- **File modified**: [desktop_agent.py](file:///d:/HELIOS_FINAL/HELIOS_FINAL/modules/desktop_agent.py)
- **Change details**:
  - Updated `open_website` to inspect the `site` parameter.
  - If the input contains a space and is not scheme-prefixed (does not start with `http://` or `https://`), it is identified as a search query rather than a clean domain.
  - Safely combines `site` and `query` parameters into a single string (collapsing double spaces) and quotes it via `urllib.parse.quote` to perform a Google search.

---

## Fix 4: Task Scheduler Expired Task Cleanup
- **File modified**: [task_scheduler.py](file:///d:/HELIOS_FINAL/HELIOS_FINAL/modules/task_scheduler.py)
- **Change details**:
  - Updated `_reschedule_active` to handle stale active tasks.
  - On startup, if an active task has a `run_at` timestamp in the past, its status is changed to `"missed"`, a log entry is emitted, and the updated database is saved to `scheduled_tasks.json`.

---

## Fix 5: Log Noise & Teardown Hooks
- **Files modified**: 
  - [score_engine.py](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/routing/score_engine.py)
  - [routing_engine.py](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/routing/routing_engine.py)
  - [agent.py](file:///d:/HELIOS_FINAL/HELIOS_FINAL/agent.py)
- **Change details**:
  - Added `verbose: bool = True` parameter to `get_effective_capability` in `score_engine.py` to suppress log output when checking capability mismatches.
  - Updated `routing_engine.py` to invoke `get_effective_capability` with `verbose=False` inside its mismatch ranking step, limiting adjustment logs to exactly one output per candidate.
  - Imported `atexit` in `agent.py` and registered `self.shutdown` during `HELIOSAgent.__init__` initialization.
  - Implemented an idempotent check flag (`self._shutdown_done`) inside `shutdown()` to prevent double execution.
