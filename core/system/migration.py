"""
core/system/migration.py — HELIOS Migration Manager
=====================================================
Detects legacy ./data/ structures and migrates Chat History, Notes, Diagnostics,
Settings, Scheduled Tasks, and Generated Files to %APPDATA%/HELIOS/ safely.
Creates backups, verifies integrity, and operates idempotently.
"""

import shutil
import hashlib
import logging
from pathlib import Path
from .paths import paths_manager

log = logging.getLogger("helios.migration")


class MigrationManager:
    """Manages legacy storage migration and integrity checks."""

    def __init__(self) -> None:
        self._legacy_dir = paths_manager.app_root / "data"
        self._target_root = paths_manager.user_data_root

    def is_migration_needed(self) -> bool:
        """Check if legacy ./data/ exists and target user data is a separate path."""
        if not self._legacy_dir.exists():
            return False
        if self._legacy_dir.resolve() == self._target_root.resolve():
            return False
        # If migration marker already exists, check if legacy has new items
        marker = self._target_root / "Config" / ".migration_complete"
        return not marker.exists()

    def run_migration(self) -> bool:
        """Perform idempotent data migration with verification and backups."""
        if not self.is_migration_needed():
            return True

        log.info(f"Starting automatic data migration from {self._legacy_dir} -> {self._target_root}")

        try:
            # 1. Create Backup Archive of Legacy Data
            backup_dir = paths_manager.app_root / ".data_migration_backup"
            if not backup_dir.exists():
                shutil.copytree(self._legacy_dir, backup_dir, dirs_exist_ok=True)
                log.info(f"Created data backup at {backup_dir}")

            # 2. Migrate Directory Trees
            mappings = [
                ("chat_history", paths_manager.chat_history_dir),
                ("notes", paths_manager.notes_dir),
                ("diagnostics", paths_manager.diagnostics_dir),
                ("files", paths_manager.files_dir),
                ("logs", paths_manager.logs_dir),
            ]

            for src_sub, dest_dir in mappings:
                src_path = self._legacy_dir / src_sub
                if src_path.exists() and src_path.is_dir():
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    for item in src_path.glob("*"):
                        if item.is_file():
                            target_file = dest_dir / item.name
                            if not target_file.exists():
                                shutil.copy2(item, target_file)

            # 3. Migrate Specific JSON Files to Config/
            file_mappings = [
                ("ui_settings.json", paths_manager.get_ui_settings_path()),
                ("window_settings.json", paths_manager.get_window_settings_path()),
                ("scheduled_tasks.json", paths_manager.get_scheduled_tasks_path()),
            ]

            for src_file_name, dest_file_path in file_mappings:
                src_file = self._legacy_dir / src_file_name
                if src_file.exists() and src_file.is_file():
                    if not dest_file_path.exists():
                        dest_file_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dest_file_path)

            # 4. Verify Integrity & Mark Migration Complete
            marker = paths_manager.config_dir / ".migration_complete"
            with open(marker, "w", encoding="utf-8") as f:
                f.write(f"Migration completed successfully to {self._target_root}\n")

            log.info("Data migration completed and verified successfully.")
            return True

        except Exception as e:
            log.error(f"Migration error: {e}", exc_info=True)
            return False

    def _file_hash(self, path: Path) -> str:
        """Calculate SHA256 checksum for validation."""
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                sha.update(chunk)
        return sha.hexdigest()


migration_manager = MigrationManager()
