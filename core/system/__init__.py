"""
core/system — HELIOS System Infrastructure Package
===================================================
Production deployment infrastructure, environment loading, path management,
dependency detection, platform abstraction, runtime context, migration, and shutdown.
"""

from .version import VersionManager, VERSION_INFO
from .platform import PlatformManager, platform_manager
from .paths import PathsManager, paths_manager
from .environment import EnvironmentManager, environment_manager
from .dependency_checker import DependencyChecker, dependency_checker
from .migration import MigrationManager, migration_manager
from .shutdown import ShutdownManager, shutdown_manager
from .runtime_manager import RuntimeManager, RuntimeContext, runtime_manager

__all__ = [
    "VersionManager", "VERSION_INFO",
    "PlatformManager", "platform_manager",
    "PathsManager", "paths_manager",
    "EnvironmentManager", "environment_manager",
    "DependencyChecker", "dependency_checker",
    "MigrationManager", "migration_manager",
    "ShutdownManager", "shutdown_manager",
    "RuntimeManager", "RuntimeContext", "runtime_manager",
]
