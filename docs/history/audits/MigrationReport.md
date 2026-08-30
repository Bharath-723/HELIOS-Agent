# HELIOS v3.5 — Data Migration Report
**Phase 2: Production Hardening**

---

## 1. Overview

`MigrationManager` (`core/system/migration.py`) provides an automatic, safe, idempotent data migration workflow for existing HELIOS installations.

---

## 2. Migration Execution Flow

1. **Trigger Check:** Evaluates whether legacy `./data/` exists and `.migration_complete` marker is missing from `%APPDATA%\HELIOS\Config\`.
2. **Safety Backup:** Copies `./data/` to `.data_migration_backup/`.
3. **Payload Migration:** Copies chat history, user notes, generated documents, telemetry diagnostics, UI drawer settings, window geometry, and scheduled tasks to `%APPDATA%\HELIOS\`.
4. **Validation Marker:** Writes `.migration_complete` marker file upon successful migration.
5. **Idempotency:** Re-running startup skips migration if `.migration_complete` is present.
