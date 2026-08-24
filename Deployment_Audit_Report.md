# HELIOS v3.5 — Deployment Audit Report
**Phase 1: Production Readiness Inspection & Audit**
**Date:** August 6, 2026
**Target Operating System:** Windows 10 / 11 (Clean Machine Installation)

---

## 1. Executive Summary

This report presents a comprehensive production readiness audit of HELIOS v3.5. The objective of this audit is to evaluate whether HELIOS can be deployed, installed, and executed cleanly on a fresh Windows system with zero pre-installed software (no Python, no Git, no C++ compilers, no Ollama).

### Audit Verdict: **NOT READY FOR PRODUCTION DEPLOYMENT**
- **Overall Readiness Score:** 4.2 / 10 (ALPHA Level)
- **Deployment Feasibility Today:** ❌ **FAILED**
- **Target User Suitability:** Non-technical users cannot install or run HELIOS in its current state.

---

## 2. Core Audit Findings & Blockers

### 2.1 Critical Blockers (Must Fix Before Packaging)

| # | Category | Description | Impact |
|---|---|---|---|
| 1 | **Installer / Packaging** | No standalone binary (`.exe`) or Windows Installer (`.msi` / InnoSetup) exists. Requires raw source checkout. | User must manually open PowerShell/CMD and install Python. |
| 2 | **Python Runtime Dependency** | Application relies on Python interpreter (`python -m venv`) and `pip install`. | Fails instantly on clean Windows machine without Python 3.10+. |
| 3 | **C-Extension Build Failures** | `requirements.txt` contains `pyaudio` and `psutil`. `pyaudio` fails `pip install` without pre-compiled wheels or Visual C++ Build Tools. | `setup.bat` fails during `pip install -r requirements.txt`. |
| 4 | **Missing Python Package** | `wmi` is imported in `ui/diagnostics_panel.py` but is **missing** from `requirements.txt`. | Telemetry falls back to degraded mode or throws `ImportError`. |
| 5 | **External Daemon Dependency** | Local LLM execution relies on Ollama running on `localhost:11434`. Ollama is not bundled or auto-installed. | App fails to answer queries offline unless user manually downloads & installs Ollama. |
| 6 | **Missing Asset Directory** | `ui/sound_manager.py` attempts to load `assets/sounds/startup.wav`, but `assets/` directory does not exist. | Startup sound fails silently. |
| 7 | **Hardcoded API Secrets** | A live Google Gemini API key (`GEMINI_API_KEY`) is hardcoded in the committed `.env` file. | Critical security leak & quota vulnerability. |
| 8 | **Path Resolution & Workdir Dependency** | Relative file paths (`data/notes`, `data/scheduled_tasks.json`, `helios.log`) assume current working directory is project root. | Launching shortcut from desktop or Program Files creates folders in arbitrary locations or throws `PermissionError`. |

---

## 3. Detailed Subsystem Audit Summaries

### 3.1 Project Structure & Cleanliness
- **Entry Points:** `helios_popup.py` (GUI) and `main.py` (CLI).
- **Core Subsystems:** `core/` (Knowledge, Reasoning, Routing engines), `modules/` (Desktop automation, Task scheduler, Voice, Search), `ui/` (Tkinter visual layer), `benchmark/` (Research evaluation suite).
- **Artifact Hygiene:** Contains leftover shell expansion typo directory `{core,modules,data/{notes,files,chat_history},tests}`.

### 3.2 Python & External Runtime Dependencies
- **Third-Party Python Packages:** 17 active packages. 7 packages in `requirements.txt` (`streamlit`, `pyperclip`, `openpyxl`, `pandas`, `beautifulsoup4`, `schedule`, `pipwin`) are un-imported bloat.
- **External Binaries:** Ollama service (`ollama.exe`), Windows Explorer (`explorer.exe`), Task Manager (`taskmgr.exe`), System Shutdown (`shutdown.exe`), Windows Registry (`winreg`).

### 3.3 Security & Privileges
- Plaintext API credentials stored in `.env`.
- System controls execute raw shell commands (`LockWorkStation`, `SetSuspendState`, `shutdown /s`).
- No elevation privilege checks before attempting registry or system modifications.

---

## 4. Phase 2 Deployment Action Plan

To transform HELIOS from an experimental source repository into a production desktop application, the following sequential roadmap must be executed in Phase 2 (Deployment Hardening):

1. **Purge Hardcoded Secrets:** Remove active API keys from `.env` and add key prompt dialogs in Settings.
2. **Fix Dependency Specifications:** Add `wmi` to `requirements.txt`, remove 7 unused bloated libraries, and lock exact wheel versions for Windows (`PyAudio` binary wheels).
3. **Bundle Assets:** Create `assets/sounds/` directory and populate missing WAV sound files.
4. **Implement Centralized Path Resolver:** Standardize path resolution using `sys._MEIPASS` / `%APPDATA%\HELIOS` instead of relative working directory paths.
5. **Implement PyInstaller / Nuitka Freeze:** Freeze Python runtime into single-folder binary (`HELIOS.exe`).
6. **Automate Ollama Bootstrap:** Package an automated installer script or embed lightweight local engine bootstrap.
7. **Build InnoSetup Installer:** Generate a standard Windows `.exe` wizard installer with Start Menu shortcuts and uninstaller support.
