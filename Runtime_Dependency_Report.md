# HELIOS v3.5 — Runtime Dependency Report
**Phase 1: Production Readiness Audit**

---

## 1. Executive Summary

HELIOS depends on multiple external software packages, Windows OS binaries, system DLLs, driver interfaces, and network services. This report classifies every external dependency by criticality and evaluates installer packaging requirements.

---

## 2. External Software Dependencies Matrix

| Software / Service | Type | Required / Optional | Minimum Version | Purpose in HELIOS | Failure Behavior if Missing | Installer Requirement |
|---|---|---|---|---|---|---|
| **Python Interpreter** | Runtime | **Required** | Python 3.10+ | Executes Python application logic. | App cannot start. | Bundle standalone Python embedded runtime or freeze via PyInstaller. |
| **Ollama Service** | Service / Daemon | **Required** (Offline Mode) | Ollama 0.1.8+ | Local LLM inference server (`gemma3`). | App falls back to cloud mode or displays connection warning. | Check for Ollama; offer auto-download wizard in setup. |
| **Ollama LLM Model** | Model Payload | **Required** (Offline Mode) | `gemma3` / `mistral` | Weights for local AI reasoning. | Ollama fails generation call; app prompts user to pull model. | Run `ollama pull gemma3` automatically during setup. |
| **Visual C++ Redistributable** | System DLL | **Required** | VC++ 2015-2022 (v140) | Native C runtime for Python wheels & DLLs. | `DLL load failed: The specified module could not be found.` | Include `vcredist_x64.exe` in Windows Installer package. |
| **Windows Explorer (`explorer.exe`)** | OS Binary | **Required** | Windows 10/11 | Opening folders, desktop files, UI shell. | File opening commands fail. | Standard Windows system binary (Always present). |
| **Windows Notepad (`notepad.exe`)** | OS Binary | Optional | Any | Opening created text files. | Text file viewing fails. | Standard Windows system binary (Always present). |
| **Task Manager (`taskmgr.exe`)** | OS Binary | Optional | Any | System controls shortcut. | Task manager shortcut fails. | Standard Windows system binary (Always present). |
| **Windows Shutdown (`shutdown.exe`)** | OS Binary | Optional | Any | System sleep/shutdown/restart commands. | Power commands fail. | Standard Windows system binary (Always present). |
| **NVIDIA Utilities (`nvidia-smi`)** | Driver Utility | Optional | Driver 450+ | GPU temperature & VRAM monitoring in Diagnostics. | Diagnostics displays `GPU: N/A`. Safe fallback handled. | Driver-dependent; check existence gracefully. |
| **Windows Registry (`winreg`)** | OS API | **Required** | Any | System light/dark theme auto-detection. | Falls back to default Dark Theme. | Standard Python Windows binding (Always present). |
| **Default Mail Client** | OS Handler | Optional | Any | `mailto:` link invocation for email drafts. | Browser opens blank `mailto:` prompt. | Standard Windows URI handler. |
| **Google Cloud API** | Cloud Service | Optional | API v1 | Cloud Gemini inference. | Network error displayed; falls back to local Ollama. | Require internet connection & valid API key. |

---

## 3. Deployment & Packaging Recommendations

1. **Standalone PyInstaller Executable:**
   - Package HELIOS as a self-contained `.exe` incorporating Python 3.10+, eliminating Python installation steps for end users.
2. **Prerequisite Verification in Installer:**
   - The installer must check for VC++ Redistributable (`vcredist_x64.exe`) and install it if missing.
3. **Ollama Installer Integration:**
   - Detect if `ollama.exe` is installed on `PATH` or at `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`.
   - If missing, prompt user to download Ollama or launch silent Ollama setup.
   - Execute `ollama pull gemma3` in background post-installation.
