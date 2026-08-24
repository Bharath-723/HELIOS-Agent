# HELIOS v3.5 — Filesystem Migration Report
**Phase 2: Production Hardening**

---

## 1. Executive Summary

This report documents the storage migration from relative project directory paths (`./data/`) to Windows AppData (`%APPDATA%\HELIOS\`) and Portable Mode (`./Data/`).

---

## 2. Directory Structure Specification

```
%APPDATA%\HELIOS\  (or ./Data/ in Portable Mode)
│
├── Config/
│   ├── .env                       (User environment overrides)
│   ├── ui_settings.json           (Saved UI drawer theme and mode settings)
│   ├── window_settings.json       (Window geometry and coordinates)
│   ├── scheduled_tasks.json       (APScheduler persisted tasks)
│   └── .migration_complete        (Migration completion marker)
│
├── Logs/
│   ├── application.log            (Main rotating application log)
│   └── crash.log                  (Crash dump log)
│
├── ChatHistory/
│   ├── index.json                 (Session index metadata)
│   └── <session_id>.json          (Per-session message turn payloads)
│
├── Notes/
│   ├── .index.json                (Notes index metadata)
│   └── <note_slug>.md             (User markdown note files)
│
├── Files/                         (Generated .docx, .pdf, .txt documents)
├── Diagnostics/                   (Telemetry exports and benchmark outputs)
├── Cache/                         (Temporary search and LLM caches)
├── Plugins/                       (User plugins and extensions)
├── Models/                        (Model metadata caches)
├── Sessions/                      (Session lock markers)
└── Temp/                          (Transient file processing directory)
```

---

## 3. Migration Mechanism (`core/system/migration.py`)

- **Detection:** On launch, `MigrationManager` checks if legacy `./data/` directory exists and `.migration_complete` marker is absent in `%APPDATA%\HELIOS\Config\`.
- **Backup:** Creates an automatic copy at `.data_migration_backup/` before starting migration.
- **Copy & Verify:** Recursively copies chat history, notes, diagnostics, generated files, and settings files to the new target.
- **Idempotency:** Migration checks file existence before copying and writes `.migration_complete` upon successful completion. Never deletes legacy source data.
