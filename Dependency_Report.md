# HELIOS v3.5 — Dependency Report
**Phase 1: Production Readiness Audit**

---

## 1. Overview

This report provides a detailed breakdown of all Python dependencies, third-party libraries, missing imports, unused packages, and platform-specific requirements across the HELIOS codebase.

---

## 2. Python Package Inventory vs requirements.txt

| Package Name | Specified in `requirements.txt` | Actually Imported | Platform | Status / Audit Notes |
|---|---|---|---|---|
| `ollama` | Yes (`>=0.1.8`) | Yes | Cross-platform | Required for local LLM IPC client API. |
| `openai` | Yes (`>=1.30.0`) | Yes | Cross-platform | Required for cloud OpenAI models (`gpt-4o-mini`). |
| `google-genai` | Yes (`>=1.0.0`) | Yes | Cross-platform | Required for cloud Gemini models (`gemini-2.0-flash`). |
| `requests` | Yes (`>=2.31.0`) | Yes | Cross-platform | Required for HTTP REST calls to Ollama & web lookups. |
| `duckduckgo-search` | Yes (`>=6.1.0`) | Yes | Cross-platform | Required for web search module (`modules/web_search.py`). |
| `apscheduler` | Yes (`>=3.10.4`) | Yes | Cross-platform | Required for background task scheduling (`modules/task_scheduler.py`). |
| `pyautogui` | Yes (`>=0.9.54`) | Yes | Windows/Desktop | Required for GUI screenshot & input automation (`modules/desktop_agent.py`). |
| `pygetwindow` | Yes (`>=0.0.9`) | Yes | Windows | Required for desktop window management (`modules/desktop_agent.py`). |
| `plyer` | Yes (`>=2.1.0`) | Yes | Cross-platform | Required for OS notification popups (`agent.py`). |
| `python-docx` | Yes (`>=1.1.0`) | Yes | Cross-platform | Required for document file generation (`modules/file_creator.py`). |
| `reportlab` | Yes (`>=4.1.0`) | Yes | Cross-platform | Required for PDF file generation (`modules/file_creator.py`). |
| `psutil` | Yes (`>=5.9.8`) | Yes | Cross-platform | Required for hardware diagnostics polling (`ui/diagnostics_panel.py`). |
| `rich` | Yes (`>=13.7.0`) | Yes | Cross-platform | Required for CLI terminal formatting (`main.py`). |
| `python-dotenv` | Yes (`>=1.0.1`) | Yes | Cross-platform | Required for `.env` loading (`core/llm_engine.py`). |
| `SpeechRecognition` | Yes (`>=3.8.1`) | Yes | Cross-platform | Required for voice input (`modules/voice_input.py`). |
| `pyaudio` | Yes (`>=0.2.11`) | Yes | Windows (C-Wheel) | **INSTALL RISK:** Fails `pip install` on clean Windows without C++ tools. |
| `wmi` | **NO (MISSING)** | **YES** | Windows-only | **MISSING DEPENDENCY:** Used in `ui/diagnostics_panel.py`. |
| `streamlit` | Yes (`>=1.35.0`) | **NO** | Cross-platform | **UNUSED BLOAT:** Adds ~150MB of unused dependencies. |
| `pyperclip` | Yes (`>=1.8.2`) | **NO** | Cross-platform | **UNUSED BLOAT:** Replaced by `tkinter` clipboard methods. |
| `openpyxl` | Yes (`>=3.1.2`) | **NO** | Cross-platform | **UNUSED BLOAT:** Never imported in project codebase. |
| `pandas` | Yes (`>=2.2.0`) | **NO** | Cross-platform | **UNUSED BLOAT:** Never imported in project codebase. Adds ~100MB. |
| `beautifulsoup4` | Yes (`>=4.12.0`) | **NO** | Cross-platform | **UNUSED BLOAT:** Web search uses direct json results. |
| `schedule` | Yes (`>=1.2.0`) | **NO** | Cross-platform | **UNUSED BLOAT:** App uses `apscheduler`, not `schedule`. |
| `pipwin` | Yes (`>=0.5.2`) | **NO** | Windows | **UNUSED BLOAT:** Referenced in docstring, never imported. |

---

## 3. Dependency Risk Analysis

### 3.1 C-Extension Installation Failure (`pyaudio`)
- **Problem:** `pyaudio` relies on PortAudio C libraries. On a clean Windows 10/11 system running `pip install pyaudio`, `pip` attempts to compile C source if wheels are mismatched, failing with `error: Microsoft Visual C++ 14.0 or greater is required`.
- **Solution for Production:** Lock explicit pre-compiled binary wheel versions or bundle wheel `.whl` files in installer payload.

### 3.2 Missing Package (`wmi`)
- **Problem:** `ui/diagnostics_panel.py` imports `wmi` to query CPU/GPU temperatures. Because `wmi` is missing from `requirements.txt`, running `setup.bat` on a clean system will leave `wmi` uninstalled.
- **Solution for Production:** Add `wmi>=1.5.1` and `pywin32>=306` to `requirements.txt`.

### 3.3 Dependency Bloat
- **Problem:** 7 unnecessary packages (`streamlit`, `pandas`, `openpyxl`, `beautifulsoup4`, `pyperclip`, `schedule`, `pipwin`) increase virtual environment size by >300 MB and slow down installation.
- **Solution for Production:** Clean `requirements.txt` to contain strictly used runtime packages.

---

## 4. Standard Library & Windows OS Dependencies

The following standard library and Windows-specific API modules are used:
- `winreg`: Reads Windows Registry (`HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize`) for system theme detection.
- `winsound`: Plays native Windows audio alerts (`MB_ICONASTERISK`).
- `ctypes`: System memory queries (`GlobalMemoryStatusEx`) and dpi awareness setup.
- `subprocess`: Windows system command execution.
