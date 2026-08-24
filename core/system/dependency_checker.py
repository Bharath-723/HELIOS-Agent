"""
core/system/dependency_checker.py — HELIOS Dependency Checker
================================================================
Performs backend checks for Python runtime, virtual environment, Ollama endpoints,
installed LLM models, system resources (CPU, RAM, Disk), GPU hardware, VC++ runtimes,
and network reachability. Returns structured DependencyStatus data.
"""

import sys
import os
import shutil
import requests
import logging
from dataclasses import dataclass
from pathlib import Path
from .platform import platform_manager
from .environment import environment_manager

log = logging.getLogger("helios.dependency_checker")


@dataclass
class DependencyStatus:
    python_ok: bool = True
    venv_ok: bool = False
    ollama_ok: bool = False
    available_models: list = None
    internet_ok: bool = False
    vcredist_ok: bool = True
    gpu_ok: bool = False
    ram_total_gb: float = 0.0
    ram_available_gb: float = 0.0
    disk_free_gb: float = 0.0
    missing_packages: list = None

    def __post_init__(self):
        if self.available_models is None:
            self.available_models = []
        if self.missing_packages is None:
            self.missing_packages = []

    @property
    def local_models(self) -> list:
        return self.available_models or []

    @property
    def ollama_available(self) -> bool:
        return self.ollama_ok


class DependencyChecker:
    """Backend dependency inspector."""

    def __init__(self) -> None:
        pass

    def inspect_all(self) -> DependencyStatus:
        status = DependencyStatus()

        # 1. Virtual Environment & Python Check
        status.python_ok = (sys.version_info >= (3, 10))
        status.venv_ok = (sys.prefix != sys.base_prefix) or ("venv" in sys.executable.lower())

        # 2. Check VC++ Runtime (Windows only)
        if platform_manager.is_windows():
            system32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
            vc_dll = system32 / "vcruntime140.dll"
            status.vcredist_ok = vc_dll.exists()
        else:
            status.vcredist_ok = True

        # 3. Internet Connectivity (Configurable, defaults to 1.1.1.1 or duckduckgo)
        status.internet_ok = self.check_internet()

        # 4. Ollama & Dynamic Model Enumeration
        ollama_url = environment_manager.get("OLLAMA_BASE_URL", "http://localhost:11434")
        status.ollama_ok, status.available_models = self.check_ollama(ollama_url)

        # 5. GPU Capability
        status.gpu_ok = platform_manager.supports_gpu()

        # 6. System Resource Metrics (psutil / shutil)
        try:
            import psutil
            mem = psutil.virtual_memory()
            status.ram_total_gb = round(mem.total / (1024**3), 2)
            status.ram_available_gb = round(mem.available / (1024**3), 2)
        except Exception:
            status.ram_total_gb = 8.0
            status.ram_available_gb = 4.0

        try:
            total, used, free = shutil.disk_usage(Path.home())
            status.disk_free_gb = round(free / (1024**3), 2)
        except Exception:
            status.disk_free_gb = 10.0

        # 7. Package Verification
        required = ["requests", "psutil", "dotenv", "wmi"]
        missing = []
        for pkg in required:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        status.missing_packages = missing

        return status

    def check_internet(self, target_url: str = "https://1.1.1.1") -> bool:
        """Configurable internet check."""
        try:
            r = requests.get(target_url, timeout=3)
            return r.status_code < 400
        except Exception:
            try:
                r2 = requests.get("https://html.duckduckgo.com", timeout=3)
                return r2.status_code < 400
            except Exception:
                return False

    def check_ollama(self, base_url: str) -> tuple[bool, list[str]]:
        """Query Ollama HTTP API /api/tags for dynamic model enumeration."""
        try:
            r = requests.get(f"{base_url}/api/tags", timeout=3)
            if r.status_code == 200:
                models_data = r.json().get("models", [])
                models = list(dict.fromkeys(m["name"].split(":")[0] for m in models_data))
                return True, models
        except Exception:
            pass
        return False, []


dependency_checker = DependencyChecker()
