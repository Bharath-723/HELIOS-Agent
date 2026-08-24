# HELIOS v3.5 — Configuration Report
**Phase 1: Production Readiness Audit**

---

## 1. Overview

This report documents all configurable settings, hardcoded variables, environment variables, relative paths, and machine-specific values across the HELIOS application.

---

## 2. Configurable Settings Inventory

| Variable Name | Location / Scope | Default Value | Configurable via | Category | Audit Notes |
|---|---|---|---|---|---|
| `OLLAMA_BASE_URL` | `.env` / `LLMEngine` | `http://localhost:11434` | `.env` file | Network / IPC | Points to local Ollama server. |
| `OLLAMA_MODEL` | `.env` / `LLMEngine` | `gemma3` (fallback `mistral`) | `.env` / UI Settings | AI Model | Default model for local inference. |
| `CLOUD_PROVIDER` | `.env` / `LLMEngine` | `gemini` | `.env` / UI Drawer | Cloud AI | Selects `gemini` or `gpt`. |
| `GEMINI_API_KEY` | `.env` / `LLMEngine` | `AIzaSyATtlJYfm...` | `.env` file | Credentials | **SECURITY RISK:** Hardcoded live key in repo. |
| `GEMINI_MODEL` | `.env` / `LLMEngine` | `gemini-2.0-flash` | `.env` file | Cloud AI | Model name for Gemini provider. |
| `OPENAI_API_KEY` | `.env` / `LLMEngine` | `your_openai_api_key_here` | `.env` file | Credentials | Template key for OpenAI provider. |
| `OPENAI_MODEL` | `.env` / `LLMEngine` | `gpt-4o-mini` | `.env` file | Cloud AI | Model name for OpenAI provider. |
| `LLM_MODE` | `.env` / `LLMEngine` | `auto` | `.env` / UI Drawer | Execution | Modes: `offline`, `online`, `auto`. |
| `TIMEZONE` | `.env` / `TaskScheduler` | `Asia/Kolkata` | `.env` file | Localization | **HARDCODED:** Hardcoded default timezone. |
| `NOTES_DIR` | `.env` / `NotesManager` | `data/notes` | `.env` file | Storage | Relative path to notes storage. |
| `FILES_DIR` | `.env` / `FileCreator` | `data/files` | `.env` file | Storage | Relative path to generated files. |
| `MAX_SEARCH_RESULTS` | `modules/web_search.py` | `5` | `.env` / Code | Search | Max search results to fetch. |

---

## 3. Path & Environment Hardcoding Issues

### 3.1 Relative Working Directory Vulnerability
- **Locations:** `data/notes`, `data/files`, `data/chat_history`, `data/diagnostics`, `data/logs`, `data/scheduled_tasks.json`, `data/ui_settings.json`, `data/window_settings.json`, `helios.log`.
- **Problem:** All paths are evaluated relative to `Path(__file__).parent.parent` or the current working directory (`os.getcwd()`).
- **Deployment Impact:** If HELIOS is installed in `C:\Program Files\HELIOS\` or launched via a desktop shortcut with a different working directory, Python will attempt to create files in `C:\Program Files\HELIOS\` (triggering `PermissionError: [Errno 13] Access is denied`) or pollute the user's desktop with `data/` subfolders.

### 3.2 Machine-Specific Hardcoding
- `TIMEZONE=Asia/Kolkata` is set as fixed default in `.env`. On machines in UTC, EST, or PST, scheduled tasks run at incorrect local times unless `.env` is manually edited.
- Sound asset path `assets/sounds/startup.wav` is hardcoded in `ui/sound_manager.py` without testing for path existence before playing.

---

## 4. Production Hardening Recommendations

1. **Implement Central Path Management (`core/paths.py`):**
   - Direct user data (settings, notes, history, logs) to `%APPDATA%\HELIOS\` on Windows.
   - Use `sys._MEIPASS` when running inside a frozen PyInstaller `.exe`.
2. **Move Credentials out of Version Control:**
   - Remove live API keys from `.env`.
   - Provide an initial setup dialog in UI for users to enter API keys securely.
3. **Auto-Detect System Timezone:**
   - Use `tzlocal` or Windows system timezone (`tzdata`) instead of hardcoding `Asia/Kolkata`.
