# HELIOS v3.5 — Configuration Migration Report
**Phase 2: Production Hardening**

---

## 1. Hardcoded Values Elimination Summary

All hardcoded relative paths, default timezones, polling intervals, timeouts, and storage file targets have been extracted and centralized into configuration systems:

- **Storage Paths:** Centralized in `PathsManager` (`core/system/paths.py`).
- **Environment & Timezone:** Managed by `EnvironmentManager` (`core/system/environment.py`).
- **UI Settings & Window Geometry:** Stored in `%APPDATA%\HELIOS\Config\ui_settings.json` and `window_settings.json`.
- **Scheduled Tasks:** Stored in `%APPDATA%\HELIOS\Config\scheduled_tasks.json`.
- **Application Logging:** Centralized under `%APPDATA%\HELIOS\Logs\application.log`.
