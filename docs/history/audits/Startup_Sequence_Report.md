# HELIOS v3.5 — Startup Sequence Report
**Phase 1: Production Readiness Audit**

---

## 1. Overview

This report documents the detailed execution flow, component initialization order, thread dispatching, blocking operations, and startup latency estimates when launching HELIOS.

---

## 2. Startup Execution Sequence

```
[User / OS Launcher]
       │
       ▼
 1. helios_popup.py entry point execution
       │
       ├─► Check Virtual Environment (Python executable path check)
       │     └─► If non-venv Python: Re-executes sub-process with ./venv/Scripts/python.exe
       │
       ├─► Import Core UI & Theme Systems (ui.theme, ui.animation_engine, ui.icon_manager)
       │
       ├─► Initialize Root Tkinter Window (overrideredirect=True, alpha=0.0 invisible)
       │
       ├─► Load Saved Settings (data/ui_settings.json & data/window_settings.json)
       │
       ├─► Query Windows Registry for System Dark/Light Theme (winreg)
       │
       ├─► Build UI Component Hierarchy:
       │     ├─► AmbientBackground Canvas
       │     ├─► Header Bar & Control Buttons
       │     ├─► NavigationRail & Tooltips
       │     ├─► Content Frame & Panel Registry (ChatView, HistoryPanel, ModelsPanel, DiagnosticsPanel)
       │     ├─► InputPanel & Circular Action Buttons
       │     └─► SettingsDrawer Overlay
       │
       ├─► Start 60 FPS Animation Engine Loop (root.after(16))
       │
       ├─► Start Diagnostics Telemetry Thread (2.0s sleep loop)
       │
       ├─► Launch Asynchronous Agent Initialization Thread:
       │     │
       │     ├─► Initialize LLMEngine (read .env, test Ollama endpoint http://localhost:11434)
       │     ├─► Load RoutingEngine & NLRouter (CAHRA ranker initialization)
       │     ├─► Load NotesManager (data/notes index scan)
       │     ├─► Initialize & Start TaskScheduler (APScheduler background thread)
       │     ├─► Initialize ChatHistory (data/chat_history session file creation)
       │     └─► Register Agent UI notify callbacks
       │
       ├─► Trigger Window Fade-In Transition (400ms alpha interpolation 0.0 -> 0.98)
       │
       └─► Play Startup Chime (SoundManager -> assets/sounds/startup.wav) [Fails silently if missing]
```

---

## 3. Detailed Component Initialization Analysis

| Order | Subsystem | File / Function | Thread | Operations Performed | Potential Blocking Risk |
|---|---|---|---|---|---|
| 1 | Python Bootstrap | `helios_popup.py:19-28` | Main | Subprocess check for venv interpreter. | Moderate: Spawns second process if run with global python. |
| 2 | Tkinter Root | `helios_popup.py:90-110` | Main UI | Creates borderless window, geometry & bindings. | Low |
| 3 | Config Load | `helios_popup.py:200-220` | Main UI | Reads `data/ui_settings.json` & `data/window_settings.json`. | Low: Exception handled with defaults. |
| 4 | Theme Sync | `ui/theme.py:280-300` | Main UI | Queries `winreg` registry key. | Low: Windows-only API; returns default dark mode if fails. |
| 5 | UI Widget Tree | `helios_popup.py:230-290` | Main UI | Instantiates full widget hierarchy. | Low-Moderate: Instantiates ~120 Tkinter widgets. |
| 6 | Animation Engine | `ui/animation_engine.py` | Main UI | Schedules `root.after(16)` 60 FPS loop. | Low |
| 7 | Diagnostics Thread | `ui/diagnostics_panel.py` | Worker Thread | Spawns background thread polling CPU/RAM/Disk via `psutil`/`wmi`. | Low |
| 8 | Agent Load | `agent.py:HELIOSAgent` | Worker Thread | Initializes `LLMEngine`, `NLRouter`, `NotesManager`, `APScheduler`, `ChatHistory`. | **HIGH:** Network check to `localhost:11434` (Ollama) has 4s timeout if server unresponsive. Offloaded to worker thread. |
| 9 | Window Fade-In | `helios_popup.py` | Main UI | Interpolates alpha 0.0 to 0.98 over 16 steps (400ms). | Low |
| 10 | Sound Playback | `ui/sound_manager.py` | Main UI | Calls `winsound.PlaySound` on `assets/sounds/startup.wav`. | Low: Missing file caught silently. |

---

## 4. Startup Performance & Bottleneck Assessment

- **Estimated Total Startup Time (Cold Boot):** 1.2s - 2.5s on modern SSD systems.
- **Primary Bottleneck:** Asynchronous Ollama service check (`requests.get("http://localhost:11434/api/tags", timeout=4)`). If Ollama is hung or starting up, timeout can cause a 4-second delay before agent status becomes ready.
- **Worker Thread Mitigation:** Agent initialization is properly isolated inside a daemon thread (`threading.Thread(target=self._init_agent)`), keeping the Tkinter UI responsive during boot.
