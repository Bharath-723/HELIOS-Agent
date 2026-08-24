# Root Cause Analysis Report

This document details the root causes for the 5 audited defects identified during the HELIOS Phase 4 popup interactive session.

---

## Bug 1: Ollama Intermittent HTTP 500
- **Symptoms**: Local inference request fails with a `500 Server Error` from the local Ollama API. The CAHRA engine successfully detects Ollama is alive (via port checks), but during model generation, the service fails.
- **Root Cause**: The local Ollama service can encounter transient resource limits (e.g., VRAM allocation glitches) or model loading delays, returning a HTTP 500 error. The `_call_local` method in `core/llm_engine.py` lacked recovery retries for server-side errors, immediately propagating the `HTTPError` to the router. The router's fallback block then called `_call_local` again under similar local settings, causing a repeated failure visible to the user.

---

## Bug 2: Feature Extractor Keyword Mappings
- **Symptoms**: The feature extractor did not flag prompts like `"search for mgit college in google"` as requiring internet.
- **Root Cause**: The keyword rules config `routing_rules.json` only contained keyword matching triggers under `freshness` for real-time keywords like `"news"`, `"weather"`, and `"today"`. General search phrases like `"search google"`, `"search youtube"`, `"search online"`, or `"open website"` were missing, resulting in `requires_internet=False` and routing decisions defaulting to LOCAL.

---

## Bug 3: Desktop Agent URL Redirection
- **Symptoms**: Browser launches with malformed URLs containing spaces, e.g. `https://www.mgit collegee.com`.
- **Root Cause**: The `open_website` method in `modules/desktop_agent.py` fell back to suffixing `.com` to site names that did not match any shortcuts. If the input contains a space, it appended `.com` directly to the spaced string and passed it to `webbrowser.open()`, producing an invalid URI without redirecting to a search engine query or performing proper URL encoding.

---

## Bug 4: Task Scheduler Expired Tasks
- **Symptoms**: Stale tasks with status `"active"` remaining in `scheduled_tasks.json` past their execution date.
- **Root Cause**: The startup method `_reschedule_active` in `modules/task_scheduler.py` only loaded and rescheduled active tasks whose `run_at` is in the future (`run_at > now`). Expired tasks whose scheduled run times occurred in the past (e.g., when the agent was offline) were skipped, leaving them in the JSON database with `"status": "active"` indefinitely.

---

## Bug 5: Duplicate Routing Score Logs
- **Symptoms**: Scoring adjustment messages (e.g., `Adjustment: Low RAM...`) are logged multiple times for every prompt.
- **Root Cause**: `get_effective_capability` in `core/routing/score_engine.py` prints informational adjustment logs unconditionally. Since `routing_engine.py` calls `get_effective_capability` twice per model per routing cycle (once in `evaluate_model_utility` and once during capability mismatch ranking), it logs redundant messages for every candidate model on every user input.
- **Missing Shutdown Logs**: Occurred because closing the popup window abruptly bypasses standard graceful shutdown handlers. Adding a Python `atexit` register hook ensures clean teardown of the scheduler background threads and logs completion under all exit codes.
