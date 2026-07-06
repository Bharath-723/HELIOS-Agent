# Release Manifest - HELIOS v1.0.1

* **Project Name**: HELIOS (Hybrid Extensible Language Intelligence Operating System)
* **Version**: HELIOS v1.0.1
* **Release Date**: 2026-07-05
* **Python Version**: Python 3.10+
* **Supported Operating System(s)**: Windows 10 / 11

---

### Major Features
1. **Hybrid LLM Engine**: Seamless fallback routing between local models (Ollama) and cloud APIs (Gemini/OpenAI).
2. **Deterministic Intent Router**: Natural language parsing into structured JSON command payloads.
3. **Local notes & Task Manager**: Integrated Markdown notes CRUD operations and APScheduler background reminder scheduling.
4. **Desktop Automation & Controls**: Win32 ctypes and PowerShell adapters for OS controls (Wi-Fi, Bluetooth, Night Light, Volume, Brightness, and Processes).
5. **Secure File Integrations**: Hardened Word DOCX / Text conversion to PDF using reportlab and python-docx, restricted to secure paths.
6. **Chat Session Transcripts**: Segmented session history logs indexed in localized JSON documents.

---

### Stability & Security Status
* **Stability**: **10.0 / 10.0**. Verified crash-proof against missing packages, shell timeouts, invalid model queries, and registry permissions.
* **Security Hardening**: Fully hardened against command injections in Powershell filters and path traversals in file creation/deletion commands. File system operations are strictly contained inside the user's home directory.

---

### Known Limitations
* Supported on Windows systems only.
* No semantic vector search (uses flat file indexes).
* Requires manual Ollama server start (`ollama serve`) for offline local routing.
* Reference [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for detailed boundaries.

---

### Baseline Purpose
HELIOS v1.0.1 serves as the official, frozen baseline implementation for all future benchmark evaluations, routing optimizations, adaptive routing research, and conference paper datasets.
