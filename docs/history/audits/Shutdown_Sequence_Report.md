# HELIOS v3.5 — Shutdown Sequence Report
**Phase 1: Production Readiness Audit**

---

## 1. Overview

This report evaluates the shutdown behavior, resource cleanup, thread termination, background scheduler disposal, file handle flushing, and crash recovery logic in HELIOS v3.5.

---

## 2. Shutdown Execution Flow

```
[User Clicks Close (✕) / Alt+F4 / Exit Menu]
       │
       ▼
 1. _on_close() called in helios_popup.py
       │
       ├─► Save Current Window Geometry -> data/window_settings.json
       │
       ├─► Save UI Settings -> data/ui_settings.json
       │
       ├─► Stop Animation Engine Loop (anim.stop() -> sets _running=False)
       │
       ├─► Stop Diagnostics Polling Thread (diag_p.stop() -> sets _running=False)
       │
       ├─► Destroy Root Tkinter Window (root.destroy())
       │
       └─► Python OS Process Exit (sys.exit(0))
```

---

## 3. Subsystem Cleanup Audit & Resource Leaks

| Subsystem / Resource | Shutdown Handling | Audit Status | Risk / Issue Description |
|---|---|---|---|
| **Tkinter Window & Widgets** | `root.destroy()` | **CLEAN** | All UI widgets and canvas buffers destroyed by OS. |
| **Animation Loop** | `anim.stop()` | **CLEAN** | Flags event loop stop; cancels pending `root.after`. |
| **Diagnostics Thread** | `diag_p.stop()` | **PARTIAL** | Sets `_running=False`. Thread is a daemon thread and terminates on main process exit. No explicit `thread.join()`. |
| **Task Scheduler (APScheduler)** | `agent.scheduler.shutdown()` | **MISSING IN POPUP** | `helios_popup.py` **never** calls `agent.shutdown()` or `scheduler.shutdown()`. APScheduler background thread is forcefully killed by process termination! |
| **Chat History Session** | `agent.history` | **CLEAN** | Chat history entries write synchronously to JSON files on each turn. |
| **Log File Handles** | `helios.log` logging handlers | **UNFLUSHED** | `logging.shutdown()` is not explicitly invoked in `_on_close()`. Buffers flush automatically on process exit, but unhandled crashes lose last logs. |
| **Ollama Server Subprocess** | External Ollama process | **INTENTIONAL LEAVE** | HELIOS connects to Ollama via HTTP; Ollama service remains running in background (expected behavior). |

---

## 4. Crash & Unexpected Termination Recovery

- **Power Interruption / Task Manager Force Kill (`taskkill /F`):**
  - **State Integrity:** Chat history JSON files write atomically per turn, preventing total chat history corruption.
  - **Scheduled Tasks Integrity:** Scheduled tasks are persisted in `data/scheduled_tasks.json`. On next startup, `TaskScheduler` reschedules active tasks cleanly.
  - **Window State:** `data/window_settings.json` retains the last cleanly closed coordinates; unexpected crashes reopen at default centered geometry (`420x700`).

---

## 5. Production Hardening Plan

1. **Explicit Cleanup Handler in `_on_close()`:**
   - Call `self.agent.shutdown()` during window exit to cleanly stop `TaskScheduler`, flush log handles, and close thread pools.
2. **Add `atexit` Cleanup Hooks:** Register a global `atexit.register(cleanup_resources)` function as a safety fallback.
