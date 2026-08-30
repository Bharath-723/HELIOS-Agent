# HELIOS v3.5 — Security Audit Report
**Phase 1: Production Readiness Audit**

---

## 1. Executive Summary

This security audit evaluates API secret management, subprocess execution risks, local privilege assumptions, cloud data transmission, and privacy controls across HELIOS v3.5.

---

## 2. Security Vulnerability Inventory

### 2.1 Hardcoded Production API Key (Severity: **CRITICAL**)
- **File:** `.env` (Line 14)
- **Vulnerability:** An active Google Gemini API key (`GEMINI_API_KEY=AIzaSyAT...`) is stored in plain text in `.env` and committed to version control.
- **Risk:** Anyone cloning or downloading the repository gains access to this API key. Adversaries can exhaust API rate limits, run up financial costs if billing is linked, or access service telemetry.
- **Remediation:** Immediately revoke the exposed key in Google AI Studio. Purge `.env` from git tracking and store credentials in user-encrypted configuration or prompt the user via UI on first launch.

### 2.2 Unsanitized Subprocess Execution (Severity: **HIGH**)
- **Files:** `modules/desktop_agent.py`, `modules/system_controls.py`, `modules/file_creator.py`
- **Vulnerability:** System control functions execute command-line processes via `subprocess.run` and `subprocess.Popen`:
  - `subprocess.run(["shutdown", "/s", "/t", str(delay)])`
  - `subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])`
  - `subprocess.Popen(["notepad.exe", str(path)])`
  - `subprocess.Popen(["explorer.exe"])`
- **Risk:** While arguments are passed as lists (mitigating raw shell interpolation vulnerabilities), intent classification models could be manipulated via prompt injection to trigger unintended system actions (e.g. locking workstation, shutting down PC, opening unauthorized executables).
- **Remediation:** Implement a strict **User Confirmation Gate (Modal Dialog)** before executing system-impacting actions (`shutdown`, `lock`, `delete_file`, `kill_process`).

### 2.3 Unencrypted Plaintext Local Storage (Severity: **MEDIUM**)
- **Files:** `data/chat_history/*.json`, `data/notes/*.md`, `data/ui_settings.json`
- **Vulnerability:** Chat history logs, note contents, and prompt logs are stored as unencrypted plain text in local JSON/MD files.
- **Risk:** Local malware or unauthorized users on shared PCs can read past conversation logs and sensitive user notes.
- **Remediation:** Provide optional local encryption (e.g. DPAPI on Windows via `ctypes` or `cryptography` fernet keys).

### 2.4 Cloud Data Privacy Warnings (Severity: **LOW / ACCEPTABLE**)
- **Files:** `agent.py`, `core/llm_engine.py`
- **Audit Findings:** HELIOS implements privacy scanning for cloud requests. If an online query contains privacy keywords ("password", "credit card", "ssn"), HELIOS raises a privacy alert.
- **Assessment:** Good baseline safety pattern.

---

## 3. Privilege & Windows Sandbox Audit

- **Elevation Requirements:** HELIOS runs with standard user privileges. It does not require Administrator rights (`runas`).
- **Windows Registry Access:** Read-only access to `HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize` (safe).
- **Network Scope:** Outbound HTTP/HTTPS connections to `http://localhost:11434` (Ollama local API), `https://generativelanguage.googleapis.com` (Gemini), `https://api.openai.com` (OpenAI), `https://html.duckduckgo.com` (Search). No inbound listening server ports are bound.
