"""
core/system/paths.py — HELIOS Paths Manager
=============================================
Central source of truth for all application filesystem locations.
Supports AppData Mode (%APPDATA%\\HELIOS\\) and Portable Mode (./Data/ when portable.flag is present).
Automatically creates missing directory structures upon request.
"""

import sys
import os
from pathlib import Path
import logging

log = logging.getLogger("helios.paths")


class PathsManager:
    """Manages all application directories and path resolutions."""

    def __init__(self, override_root: Path | None = None) -> None:
        self._app_root = self._detect_app_root()
        self._is_portable = self._detect_portable_mode()
        
        if override_root:
            self._user_data_root = override_root
        elif self._is_portable:
            self._user_data_root = self._app_root / "Data"
        else:
            self._user_data_root = self._detect_appdata_root()

        self._ensure_directory_structure()

    # ── Root Detection ────────────────────────────────────────────────────────
    def _detect_app_root(self) -> Path:
        """Locate root directory of the HELIOS application."""
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(sys.executable).parent
        # Source execution: core/system/paths.py -> root is 2 levels up
        return Path(__file__).resolve().parent.parent.parent

    def _detect_portable_mode(self) -> bool:
        """Check if portable.flag exists in the application root."""
        flag_file = self._app_root / "portable.flag"
        return flag_file.exists()

    def _detect_appdata_root(self) -> Path:
        """Locate %APPDATA%/HELIOS on Windows or ~/.config/HELIOS on POSIX."""
        if sys.platform.startswith("win"):
            appdata = os.environ.get("APPDATA")
            if appdata:
                return Path(appdata) / "HELIOS"
            return Path.home() / "AppData" / "Roaming" / "HELIOS"
        elif sys.platform.startswith("darwin"):
            return Path.home() / "Library" / "Application Support" / "HELIOS"
        else:
            return Path.home() / ".config" / "HELIOS"

    # ── Directory Auto-Creation ───────────────────────────────────────────────
    def _ensure_directory_structure(self) -> None:
        """Ensure all required runtime subdirectories exist."""
        subdirs = [
            "Config",
            "Logs",
            "Cache",
            "ChatHistory",
            "Notes",
            "Diagnostics",
            "Files",
            "Plugins",
            "Models",
            "Sessions",
            "Temp",
        ]
        for d in subdirs:
            p = self._user_data_root / d
            p.mkdir(parents=True, exist_ok=True)

    # ── Public Accessors ──────────────────────────────────────────────────────
    @property
    def is_portable(self) -> bool:
        return self._is_portable

    @property
    def app_root(self) -> Path:
        return self._app_root

    @property
    def user_data_root(self) -> Path:
        return self._user_data_root

    @property
    def assets_dir(self) -> Path:
        p = self._app_root / "assets"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def config_dir(self) -> Path:
        return self._user_data_root / "Config"

    @property
    def logs_dir(self) -> Path:
        return self._user_data_root / "Logs"

    @property
    def cache_dir(self) -> Path:
        return self._user_data_root / "Cache"

    @property
    def chat_history_dir(self) -> Path:
        return self._user_data_root / "ChatHistory"

    @property
    def notes_dir(self) -> Path:
        return self._user_data_root / "Notes"

    @property
    def diagnostics_dir(self) -> Path:
        return self._user_data_root / "Diagnostics"

    @property
    def files_dir(self) -> Path:
        return self._user_data_root / "Files"

    @property
    def plugins_dir(self) -> Path:
        return self._user_data_root / "Plugins"

    @property
    def models_dir(self) -> Path:
        return self._user_data_root / "Models"

    @property
    def sessions_dir(self) -> Path:
        return self._user_data_root / "Sessions"

    @property
    def temp_dir(self) -> Path:
        return self._user_data_root / "Temp"

    # Specific File Helpers
    def get_ui_settings_path(self) -> Path:
        return self.config_dir / "ui_settings.json"

    def get_window_settings_path(self) -> Path:
        return self.config_dir / "window_settings.json"

    def get_scheduled_tasks_path(self) -> Path:
        return self.config_dir / "scheduled_tasks.json"

    def get_main_log_path(self) -> Path:
        return self.logs_dir / "application.log"


paths_manager = PathsManager()
