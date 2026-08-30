# HELIOS v3.5 — Deployment Risk Report
**Phase 1: Production Readiness Audit**

---

## 1. Overview

This report identifies and categorizes all risks associated with deploying HELIOS to non-technical users on clean Windows desktop environments.

---

## 2. Risk Matrix & Prioritized Findings

| Risk ID | Category | Severity | Probability | Risk Summary | Impact on End User | Mitigation Strategy |
|---|---|---|---|---|---|---|
| **RISK-01** | Installer | **CRITICAL** | **100%** | No installer package (`.exe`/`.msi`) exists. Users must install Python manually. | Non-technical users cannot install the application. | Build an InnoSetup installer wrapper bundling PyInstaller binary. |
| **RISK-02** | Runtime | **CRITICAL** | **100%** | Dependency on local Ollama service (`gemma3` model). Ollama is absent on clean Windows. | App cannot perform local AI reasoning offline; queries fail. | Automate Ollama check/installer wizard; bundle pull script. |
| **RISK-03** | Build | **HIGH** | **90%** | `pyaudio` compilation failure during `pip install -r requirements.txt`. | Setup script aborts with C++ compiler error. | Include pre-compiled binary `.whl` files or lock wheel versions. |
| **RISK-04** | Code | **HIGH** | **100%** | `wmi` library missing from `requirements.txt`. | Diagnostics panel runs in degraded mode or throws `ImportError`. | Add `wmi>=1.5.1` to `requirements.txt`. |
| **RISK-05** | Security | **HIGH** | **100%** | Live Google Gemini API key exposed in committed `.env` file. | API quota exhaustion, financial billing risk, security leak. | Revoke key; store keys in `%APPDATA%\HELIOS\config.json`. |
| **RISK-06** | Permissions | **HIGH** | **80%** | App writes runtime data to `data/` in current working directory instead of `%APPDATA%`. | Fails with `PermissionError` if installed in `C:\Program Files\`. | Redirect runtime writes to `%APPDATA%\HELIOS\`. |
| **RISK-07** | Assets | **MEDIUM** | **100%** | `assets/sounds/startup.wav` missing from project tree. | Audio chime fails silently (no sound played). | Populate `assets/sounds/startup.wav` or remove sound call. |
| **RISK-08** | UX | **MEDIUM** | **50%** | Hardcoded `TIMEZONE=Asia/Kolkata` in default config. | Scheduled tasks execute at wrong times on non-Indian PCs. | Auto-detect system timezone using `tzlocal` / Windows API. |

---

## 3. High-Priority Deployment Failure Scenarios

### Scenario A: User Launches Application from Desktop Shortcut
- **Trigger:** User installs HELIOS to `C:\Program Files\HELIOS\` and double-clicks Desktop shortcut without setting working directory.
- **Result:** `os.getcwd()` evaluates to `C:\Users\<User>\Desktop` or `C:\Program Files\HELIOS\`. Attempting to write `helios.log` or `data/ui_settings.json` fails with `PermissionError` or creates data folders on user's desktop.

### Scenario B: User Runs `setup.bat` on Clean Windows 11 PC
- **Trigger:** User double-clicks `setup.bat`.
- **Result:**
  1. `python` command fails if Python is not installed or not added to system `PATH`.
  2. `pip install -r requirements.txt` fails on `pyaudio` with `error: Microsoft Visual C++ 14.0 or greater is required`.
  3. Setup aborts prematurely.
