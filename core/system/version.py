"""
core/system/version.py — HELIOS Version Manager
=================================================
Centralizes versioning, build numbers, release channels, git commit IDs,
and runtime environment metadata.
"""

import sys
import platform
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VersionInfo:
    version: str = "3.5.0"
    build: str = "35001"
    release_channel: str = "production-hardening"
    git_commit: str = "HEAD"
    build_date: str = "2026-08-06"
    app_name: str = "HELIOS AI Operating System"


VERSION_INFO = VersionInfo()


class VersionManager:
    """Central interface for querying application version and build metadata."""

    def __init__(self, info: VersionInfo = VERSION_INFO) -> None:
        self._info = info

    @property
    def version(self) -> str:
        return self._info.version

    @property
    def build(self) -> str:
        return self._info.build

    @property
    def release_channel(self) -> str:
        return self._info.release_channel

    @property
    def git_commit(self) -> str:
        return self._info.git_commit

    @property
    def build_date(self) -> str:
        return self._info.build_date

    @property
    def full_version_string(self) -> str:
        return f"HELIOS v{self._info.version} (Build {self._info.build}-{self._info.release_channel})"

    def get_runtime_specs(self) -> dict:
        return {
            "app_version": self._info.version,
            "build": self._info.build,
            "channel": self._info.release_channel,
            "git_commit": self._info.git_commit,
            "build_date": self._info.build_date,
            "python_version": platform.python_version(),
            "python_compiler": platform.python_compiler(),
            "platform": sys.platform,
            "architecture": platform.machine(),
        }


version_manager = VersionManager()
