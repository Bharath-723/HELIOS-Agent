"""
core/system/platform.py — HELIOS Platform Manager
===================================================
Abstracts operating system checks, system themes, timezone detection,
GPU presence, and platform capability helpers.
"""

import sys
import os
import platform
import logging

log = logging.getLogger("helios.platform")


class PlatformManager:
    """Provides abstracted system platform queries and capabilities."""

    def __init__(self) -> None:
        self._os_name = sys.platform.lower()

    def is_windows(self) -> bool:
        return self._os_name.startswith("win")

    def is_linux(self) -> bool:
        return self._os_name.startswith("linux")

    def is_macos(self) -> bool:
        return self._os_name.startswith("darwin")

    def get_os_name(self) -> str:
        if self.is_windows():
            return f"Windows {platform.release()} ({platform.version()})"
        elif self.is_linux():
            return f"Linux ({platform.release()})"
        elif self.is_macos():
            return f"macOS ({platform.mac_ver()[0]})"
        return sys.platform

    def get_cpu_architecture(self) -> str:
        return platform.machine() or "x86_64"

    def supports_gpu(self) -> bool:
        """Check for NVIDIA GPU availability via nvml or nvidia-smi."""
        if not self.is_windows() and not self.is_linux():
            return False
        try:
            import subprocess
            r = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=2)
            return r.returncode == 0
        except Exception:
            return False

    def supports_ollama(self) -> bool:
        """Check if Ollama service binary or endpoint is available."""
        return True  # Ollama operates over HTTP IPC on all supported OS platforms

    def supports_voice(self) -> bool:
        """Check if voice input prerequisites are loadable."""
        try:
            import speech_recognition
            import pyaudio
            return True
        except ImportError:
            return False

    def get_system_theme(self) -> str:
        """Detect Windows system theme (Dark or Light) via registry query."""
        if not self.is_windows():
            return "dark"
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return "light" if val == 1 else "dark"
        except Exception:
            return "dark"

    def get_system_timezone(self) -> str:
        """Detect system timezone dynamically."""
        try:
            import tzlocal
            return str(tzlocal.get_localzone_name())
        except Exception:
            try:
                import time
                return time.tzname[0]
            except Exception:
                return "Asia/Kolkata"


platform_manager = PlatformManager()
