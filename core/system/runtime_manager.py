"""
core/system/runtime_manager.py — HELIOS Runtime Manager
=========================================================
Orchestrates application initialization, environment loading, dependency inspection,
migration execution, and exposes a unified RuntimeContext object.
"""

import logging
from dataclasses import dataclass
from .version import VersionManager, version_manager
from .platform import PlatformManager, platform_manager
from .paths import PathsManager, paths_manager
from .environment import EnvironmentManager, environment_manager
from .dependency_checker import DependencyChecker, DependencyStatus, dependency_checker
from .migration import MigrationManager, migration_manager

log = logging.getLogger("helios.runtime")


@dataclass
class RuntimeContext:
    """Unified container representing the active HELIOS application runtime status."""
    version: VersionManager
    platform: PlatformManager
    paths: PathsManager
    environment: EnvironmentManager
    dependencies: DependencyStatus
    migration_completed: bool
    startup_ok: bool
    capabilities: dict

    def summary_string(self) -> str:
        return (
            f"HELIOS v{self.version.version} [{self.version.release_channel}] | "
            f"OS: {self.platform.get_os_name()} | "
            f"Mode: {self.environment.get('LLM_MODE')} | "
            f"Ollama: {'OK' if self.dependencies.ollama_ok else 'UNAVAILABLE'} | "
            f"Internet: {'ONLINE' if self.dependencies.internet_ok else 'OFFLINE'}"
        )


class RuntimeManager:
    """Main orchestrator constructing RuntimeContext."""

    def __init__(self) -> None:
        self._context: RuntimeContext | None = None

    def initialize_runtime(self) -> RuntimeContext:
        """Execute full runtime setup sequence."""
        log.info("Initializing HELIOS Runtime Infrastructure...")

        # 1. Environment & Paths are loaded automatically on import
        # 2. Run Data Migration if needed
        migration_ok = migration_manager.run_migration()

        # 3. Perform Backend Dependency Inspection
        dep_status = dependency_checker.inspect_all()

        # 4. Configure Centralized Log File Handlers
        self._setup_logging()

        # 5. Build Capabilities Summary
        capabilities = {
            "is_windows": platform_manager.is_windows(),
            "supports_gpu": platform_manager.supports_gpu(),
            "supports_voice": platform_manager.supports_voice(),
            "ollama_available": dep_status.ollama_ok,
            "internet_available": dep_status.internet_ok,
            "local_models": dep_status.available_models,
            "mode": environment_manager.get("LLM_MODE"),
        }

        self._context = RuntimeContext(
            version=version_manager,
            platform=platform_manager,
            paths=paths_manager,
            environment=environment_manager,
            dependencies=dep_status,
            migration_completed=migration_ok,
            startup_ok=True,
            capabilities=capabilities,
        )

        log.info(f"Runtime Context Initialized: {self._context.summary_string()}")
        return self._context

    def get_context(self) -> RuntimeContext:
        if self._context is None:
            return self.initialize_runtime()
        return self._context

    def _setup_logging(self) -> None:
        """Configure rotating log file handlers under AppData / Logs."""
        try:
            log_file = paths_manager.get_main_log_path()
            root_logger = logging.getLogger()
            
            # Check if file handler is already attached
            has_file_h = any(isinstance(h, logging.FileHandler) for h in root_logger.handlers)
            if not has_file_h:
                fh = logging.FileHandler(log_file, encoding="utf-8")
                fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s", "%H:%M:%S")
                fh.setFormatter(fmt)
                root_logger.addHandler(fh)
                root_logger.setLevel(logging.INFO)
                log.info(f"Centralized logging output routed to {log_file}")
        except Exception as e:
            print(f"Failed to setup centralized file logger: {e}")


runtime_manager = RuntimeManager()
