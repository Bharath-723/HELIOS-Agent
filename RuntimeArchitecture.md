# HELIOS v3.5 — Runtime Architecture Specification
**Phase 2: Production Hardening**

---

## 1. System Architecture Overview

The HELIOS infrastructure is organized into a modular layered architecture separating System Primitives, AI Engines, Desktop Modules, and UI Presentation.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           HELIOS UI Presentation Layer                         │
│   (helios_popup.py / ChatView / NavigationRail / InputPanel / SettingsDrawer)  │
└──────────────────────────────────────┬─────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼─────────────────────────────────────────┐
│                       HELIOS Agent & Orchestrator                              │
│         (agent.py / NLRouter / RoutingEngine / CAHRA Ranker / LLMEngine)       │
└──────────────────────────────────────┬─────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼─────────────────────────────────────────┐
│                      System Infrastructure Layer (core/system/)                │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                            RuntimeManager                                │  │
│  │                        (RuntimeContext Object)                           │  │
│  └───────┬──────────────┬──────────────┬──────────────┬──────────────┬──────┘  │
│          │              │              │              │              │         │
│  ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐  │
│  │ PathsManager │ │ Environment│ │ Dependency │ │ Platform   │ │ Version    │  │
│  │ (AppData vs  │ │ Manager    │ │ Checker    │ │ Manager    │ │ Manager    │  │
│  │  Portable)   │ │ (.env/Local│ │ (Ollama/   │ │ (OS/Theme/ │ │ (v3.5.0/   │  │
│  │              │ │  Fallback) │ │ GPU/VC++)  │ │ Timezone)  │ │ Build)     │  │
│  └──────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
│  ┌──────────────┐ ┌────────────┐                                               │
│  │ Migration    │ │ Shutdown   │                                               │
│  │ Manager      │ │ Manager    │                                               │
│  └──────────────┘ └────────────┘                                               │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Runtime Subsystem Specifications

### 2.1 PathsManager (`core/system/paths.py`)
- Standardizes directory resolutions.
- Automatically selects `%APPDATA%\HELIOS\` on Windows or `./Data/` if `portable.flag` exists.
- Exposes immutable properties: `config_dir`, `logs_dir`, `cache_dir`, `chat_history_dir`, `notes_dir`, `diagnostics_dir`, `files_dir`, `plugins_dir`, `models_dir`, `sessions_dir`, `temp_dir`.

### 2.2 EnvironmentManager (`core/system/environment.py`)
- Searches `.env` in priority order: AppData Config -> Portable Config -> App Root -> Built-in Defaults.
- Masks API keys in logs and auto-switches `LLM_MODE` to `offline` if cloud keys are missing.

### 2.3 DependencyChecker (`core/system/dependency_checker.py`)
- Inspects Python 3.10+ runtime, venv, VC++ redistributable DLLs (`vcruntime140.dll`), GPU via `nvidia-smi`, RAM, and free disk space.
- Queries Ollama `/api/tags` HTTP endpoint for dynamic model enumeration.

### 2.4 PlatformManager (`core/system/platform.py`)
- Provides OS identification, theme detection via Windows Registry (`winreg`), and timezone detection via `tzlocal`.

### 2.5 ShutdownManager (`core/system/shutdown.py`)
- Manages idempotent cleanup, stopping APScheduler background jobs, ending worker threads, clearing temp files, and flushing logging file handlers.
