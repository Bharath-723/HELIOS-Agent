# HELIOS v3.5 — Filesystem Report
**Phase 1: Production Readiness Audit**

---

## 1. Overview

This report documents all file system interactions performed by HELIOS, detailing created folders, generated files, log targets, permission requirements, failure handling, and auto-recovery behavior.

---

## 2. Directories & Files Inventory

| Path | Purpose | Creation Timing | Write Frequency | Permissions Required | Failure Recovery Mechanism |
|---|---|---|---|---|---|
| `data/` | Main application data root container. | Startup | On state update | Read/Write | Auto-created via `os.makedirs(exist_ok=True)`. |
| `data/notes/` | Markdown files storing user notes. | On first note create | Per note creation | Read/Write | Auto-created if missing. |
| `data/files/` | Generated documents (.pdf, .docx, .txt). | On file generation | Per generation call | Read/Write | Auto-created if missing. |
| `data/chat_history/` | JSON files per chat session. | On session start | Per turn / message | Read/Write | Auto-created if missing. |
| `data/diagnostics/` | Saved diagnostic logs and benchmark outputs. | On diagnostic export | On demand | Read/Write | Auto-created if missing. |
| `data/logs/` | System logging folder. | Startup | Streaming log lines | Read/Write | Auto-created if missing. |
| `data/scheduled_tasks.json` | Persisted scheduled tasks index. | On task add/cancel | Per schedule change | Read/Write | Re-created as empty list if corrupt/missing. |
| `data/ui_settings.json` | Saved UI drawer settings (theme, mode). | On drawer change/exit | On settings edit | Read/Write | Defaults loaded if missing/corrupt. |
| `data/window_settings.json` | Window geometry & coordinates (x, y, w, h). | On window drag/close | On move / exit | Read/Write | Centered defaults used if missing. |
| `helios.log` | Root log file. | Startup | Continuous | Read/Write | Appends to existing log file. |

---

## 3. Filesystem Audit & Risk Evaluation

### 3.1 Permission Vulnerability in Multi-User & Read-Only Installation Directories
- **Problem:** In a standard Windows desktop installation (`C:\Program Files\HELIOS\` or `C:\Program Files (x86)\HELIOS\`), standard Windows user accounts do **NOT** have write permissions to the application directory.
- **Current Behavior:** HELIOS writes directly to `data/` relative to working directory / application root.
- **Failure Mode:** Running HELIOS as a standard user from `C:\Program Files\HELIOS\` triggers `PermissionError: [Errno 13] Access is denied` when trying to create `helios.log` or `data/ui_settings.json`, causing app crash at startup!

### 3.2 Malformed Artifact Folders in Repository
- The workspace contains a malformed directory created by shell expansion typo: `{core,modules,data/{notes,files,chat_history},tests}`.
- **Impact:** Clean repository packaging must exclude this malformed folder artifact.

---

## 4. Production Hardening Plan

1. **Standardize User Storage Path to Windows `%APPDATA%`:**
   - Redirect all runtime data writes (`notes`, `files`, `chat_history`, `settings`, `logs`) to `%APPDATA%\HELIOS\` (e.g. `C:\Users\<User>\AppData\Roaming\HELIOS\`).
   - Leave the application installation folder (`C:\Program Files\HELIOS\`) strictly **read-only**.
2. **Implement File Sanitization & Locking:**
   - Add file lock handling (`portalocker` or `.lock` sidecar files) for JSON settings files to prevent corruption if multiple instances run simultaneously.
