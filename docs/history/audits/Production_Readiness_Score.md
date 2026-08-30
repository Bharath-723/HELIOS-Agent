# HELIOS v3.5 — Production Readiness Scorecard
**Phase 1: Production Readiness Audit**

---

## 1. Subsystem Evaluation Matrix

Each evaluation category is scored on a scale from **1 (Unusable / Fails) to 10 (Production Grade)** based on empirical audit findings.

| Category | Score (1-10) | Weighted Weight | Key Audit Observations |
|---|---|---|---|
| **Project Structure** | **6 / 10** | 10% | Clear module separation (`core/`, `modules/`, `ui/`), but contains leftover shell expansion typo directory. |
| **Dependency Management** | **3 / 10** | 10% | `wmi` is missing from `requirements.txt`; `pyaudio` fails C-wheel compilation; 7 packages are unused bloat. |
| **Configuration Management** | **4 / 10** | 10% | Relative path bindings break if launched outside root directory; hardcoded timezone `Asia/Kolkata`. |
| **Security** | **3 / 10** | 15% | **Critical:** Active Google Gemini API key hardcoded in `.env` committed to repo; plaintext local storage. |
| **Startup Reliability** | **6 / 10** | 10% | Clean GUI initialization with 60 FPS animation loop, but 4s network timeout if Ollama is unresponsive. |
| **Shutdown Cleanliness** | **5 / 10** | 5% | `helios_popup.py` kills background scheduler threads abruptly without calling `agent.shutdown()`. |
| **Error Handling & Resilience** | **6 / 10** | 10% | High coverage of UI exception fallbacks, but hides underlying missing dependencies (silent WMI/sound fails). |
| **Deployment & Packaging** | **1 / 10** | 15% | **Zero installer / zero standalone binary packaging.** Requires raw Python environment & manual terminal setup. |
| **Maintainability** | **7 / 10** | 5% | Well-documented modular architecture (`CAHRA`, `RoutingEngine`, `NLRouter`, `ThemeManager`). |
| **Portability** | **4 / 10** | 5% | Relies heavily on Windows OS APIs (`winreg`, `winsound`, `pygetwindow`, `pyautogui`); missing cross-platform abstractions. |
| **Installer Readiness** | **1 / 10** | 5% | No InnoSetup/MSI script, no prerequisite check for Ollama or VC++ Redistributable. |

---

## 2. Score Summary & Final Level Classification

### Overall Production Readiness Score: **4.2 / 10**

```
 0.0                      4.2                             10.0
 [─────────────────────────▲───────────────────────────────]
  UNUSABLE             ALPHA / EARLY BETA         PRODUCTION READY
```

### Readiness Level Classification: **ALPHA**

- **Definition:** The software functions correctly when run by developers in a pre-configured Python workspace, but lacks packaging, installer automation, hardened configuration, security purging, and environment isolation required for end-user deployment.

---

## 3. Final Audit Verdict & Executive Answers

### 1. Can HELIOS be deployed today?
**NO.** HELIOS cannot be deployed to non-technical users today because it has no installer or executable binary and requires manual Python and Ollama setup.

### 2. What are the biggest deployment blockers?
1. Absence of a packaged executable (`.exe`) or Windows Installer (`.msi`).
2. Hardcoded local data paths (`data/`) that fail with `PermissionError` when installed in `C:\Program Files\`.
3. Hardcoded production API key in `.env` committed to version control.
4. Dependency installation failure (`pyaudio` compilation) on clean Windows machines.
5. External dependency on unbundled Ollama LLM server.

### 3. What must be fixed before packaging?
1. Purge `GEMINI_API_KEY` from `.env` and version control.
2. Add `wmi` to `requirements.txt` and remove 7 unused dependencies (`streamlit`, `pandas`, `openpyxl`, `beautifulsoup4`, `pyperclip`, `schedule`, `pipwin`).
3. Add `assets/sounds/startup.wav` to fix missing audio asset.
4. Implement centralized path resolution pointing user data to `%APPDATA%\HELIOS\`.
5. Add explicit cleanup calls (`agent.shutdown()`) in `_on_close()`.

### 4. What should the installer automate?
1. Detect and install Visual C++ Redistributable if missing.
2. Check for Ollama; offer a one-click wizard to download Ollama and execute `ollama pull gemma3`.
3. Create Desktop and Start Menu shortcuts pointing to `HELIOS.exe`.
4. Create an uninstaller entry in Windows Control Panel.

### 5. Prioritized Findings Table

| Priority Level | Finding Summary |
|---|---|
| **CRITICAL** | Package executable (`HELIOS.exe`) via PyInstaller; Revoke & purge exposed `GEMINI_API_KEY`; Redirect runtime data paths to `%APPDATA%\HELIOS\`. |
| **HIGH** | Add `wmi` to `requirements.txt`; Provide pre-compiled binary wheel for `pyaudio`; Automate Ollama check/installer. |
| **MEDIUM** | Remove 7 unused packages from `requirements.txt`; Add missing `assets/sounds/` sound files; Add clean `agent.shutdown()` call to window exit. |
| **LOW** | Auto-detect system timezone instead of hardcoded `Asia/Kolkata`; Remove malformed shell expansion folder artifact. |
