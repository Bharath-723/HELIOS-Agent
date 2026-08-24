# HELIOS v3.5 — Environment Report
**Phase 1: Production Readiness Audit**

---

## 1. Overview

This report details every environment variable referenced in the HELIOS codebase, documenting its purpose, required vs optional status, default value, failure behavior, missing variable handling, and security implications.

---

## 2. Environment Variables Inventory

| Variable Name | Code Location | Required / Optional | Default Value | Purpose | Failure Behavior if Missing | Security / Audit Notes |
|---|---|---|---|---|---|---|
| `OLLAMA_BASE_URL` | `core/llm_engine.py:47` | Optional | `http://localhost:11434` | Address of local Ollama HTTP API service. | Falls back to `http://localhost:11434`. | Non-sensitive local URL. |
| `OLLAMA_MODEL` | `core/llm_engine.py:48` | Optional | `mistral` / `gemma3` | Model tag for local LLM requests. | Falls back to `mistral`. | Non-sensitive string. |
| `LLM_MODE` | `core/llm_engine.py:49` | Optional | `offline` (code) / `auto` (`.env`) | Mode switch: `offline`, `online`, `auto`. | Defaults to `offline`. | Non-sensitive string. |
| `CLOUD_PROVIDER` | `core/llm_engine.py:60` | Optional | `gemini` | Cloud provider selection (`gemini` or `gpt`). | Defaults to `gemini`. | Non-sensitive string. |
| `GEMINI_API_KEY` | `core/llm_engine.py:56` | Required for Gemini Cloud | `""` (Empty fallback in code) | Authentication token for Google Gemini AI. | Cloud requests fail with HTTP 401/403. | **CRITICAL RISK:** Hardcoded active key present in committed `.env`. |
| `GEMINI_MODEL` | `core/llm_engine.py:57` | Optional | `gemini-2.0-flash` | Gemini model variant name. | Defaults to `gemini-2.0-flash`. | Non-sensitive string. |
| `OPENAI_API_KEY` | `core/llm_engine.py:52` | Required for OpenAI Cloud | `""` (Empty fallback in code) | Authentication token for OpenAI GPT API. | OpenAI cloud requests fail with HTTP 401. | Key template present in `.env`. |
| `OPENAI_MODEL` | `core/llm_engine.py:53` | Optional | `gpt-4o-mini` | OpenAI model variant name. | Defaults to `gpt-4o-mini`. | Non-sensitive string. |
| `TIMEZONE` | `modules/task_scheduler.py:23` | Optional | `Asia/Kolkata` | Timezone for APScheduler task execution. | Defaults to `Asia/Kolkata`. | Non-sensitive string. |
| `NOTES_DIR` | `modules/notes_manager.py:12` | Optional | `data/notes` (relative) | Path to user notes markdown files. | Defaults to `./data/notes`. | Sensitive: Stores personal user notes. |
| `FILES_DIR` | `modules/file_creator.py` | Optional | `data/files` (relative) | Path to generated user documents. | Defaults to `./data/files`. | Sensitive: Stores generated docs. |
| `MAX_SEARCH_RESULTS` | `modules/web_search.py:7` | Optional | `5` | Cap on returned DuckDuckGo search links. | Defaults to `5`. | Non-sensitive integer. |
| `PUBLIC` | `modules/desktop_agent.py:542` | Windows OS System | `C:\Users\Public` | Resolves Public Desktop path. | Falls back to `C:\Users\Public`. | Standard Windows OS environment variable. |
| `APPDATA` | `modules/desktop_agent.py:543` | Windows OS System | `""` | Resolves User AppData Roaming path. | Falls back to empty path; app lookup degrades. | Standard Windows OS environment variable. |
| `ALLUSERSPROFILE` | `modules/desktop_agent.py:544` | Windows OS System | `C:\ProgramData` | Resolves ProgramData directory. | Falls back to `C:\ProgramData`. | Standard Windows OS environment variable. |

---

## 3. Findings & Security Audit

1. **Hardcoded Gemini API Key in `.env`:**
   - Line 14 of `.env` contains an active Google Gemini key (`GEMINI_API_KEY=AIzaSyAT...`).
   - **Risk:** High security vulnerability. Anyone checking out the repository receives this key, which can lead to quota exhaustion, API revocation, or unauthorized data transmission.
2. **Lack of User-Level Environment Isolation:**
   - App relies on `.env` file located directly in application root directory.
   - In a packaged installation (`C:\Program Files\HELIOS`), standard users cannot modify `.env` without Administrator rights.
3. **Missing Variable Handling:**
   - All custom environment variables implement reasonable string fallbacks via `os.getenv("VAR", "default")`.
   - However, missing API keys cause cloud requests to throw runtime exceptions rather than cleanly prompting the user for setup in the UI.

---

## 4. Production Hardening Plan

1. **Remove `.env` from Git tracking and purge hardcoded keys.**
2. **Store User Settings in `%APPDATA%\HELIOS\config.json`** instead of relying on `.env` files in root directory.
3. **Add GUI API Key Setup Dialog:** Show an initial setup prompt if no valid API key or local Ollama model is found.
