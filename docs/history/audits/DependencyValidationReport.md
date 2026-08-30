# HELIOS v3.5 — Dependency Validation Report
**Phase 2: Production Hardening**

---

## 1. Overview

`DependencyChecker` performs dynamic backend detection for runtime environment health, installed software, and hardware capabilities.

---

## 2. Dynamic Detection Matrix

| Inspector Component | Detection Method | Output Data | Failure Mitigation |
|---|---|---|---|
| **Python & Venv** | `sys.version_info` & `sys.prefix` | Python version, Venv boolean | Warns if running Python < 3.10. |
| **Ollama Service & Models** | HTTP GET `http://localhost:11434/api/tags` | Active status, model tags list | Switches UI status to `Ollama Unavailable`; falls back to Cloud if configured. |
| **Network Reachability** | HTTP GET `https://1.1.1.1` & `https://html.duckduckgo.com` | Internet boolean | Disables web search tools if offline. |
| **GPU Capabilities** | Execution of `nvidia-smi` | GPU boolean | Disables GPU telemetry dials in Diagnostics Panel. |
| **VC++ Runtime** | Existence check of `C:\Windows\System32\vcruntime140.dll` | VC++ boolean | Logs warning if VC++ redistributable DLL is absent. |
| **RAM & Disk Space** | `psutil.virtual_memory()` & `shutil.disk_usage()` | Total/Available RAM (GB), Free Disk (GB) | Displays resource gauges in Diagnostics Panel. |
