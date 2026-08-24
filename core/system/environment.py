"""
core/system/environment.py — HELIOS Environment Manager
==========================================================
Safely loads environment configurations from AppData, Portable, or Root paths,
validates variables, masks secrets in logs, and automatically falls back to
Local Mode if cloud credentials are absent.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from .paths import paths_manager
from .platform import platform_manager

log = logging.getLogger("helios.environment")


class EnvironmentManager:
    """Manages application environment configuration and fallback logic."""

    def __init__(self) -> None:
        self._env_path: Path | None = None
        self._config: dict[str, str] = {}
        self.load_environment()

    def load_environment(self) -> None:
        """Locate and load .env configuration following strict priority order."""
        search_paths = [
            paths_manager.config_dir / ".env",
            paths_manager.app_root / "Data" / "Config" / ".env",
            paths_manager.app_root / ".env",
        ]

        found_path = None
        for p in search_paths:
            if p.exists():
                found_path = p
                break

        if found_path:
            self._env_path = found_path
            load_dotenv(dotenv_path=found_path, override=True)
            log.info(f"Loaded environment configuration from {found_path}")
        else:
            log.info("No .env file found; utilizing built-in default environment configuration.")

        self._read_and_validate()

    def _read_and_validate(self) -> None:
        """Parse, sanitize, and validate environment settings."""
        self._config = {
            "OLLAMA_BASE_URL":   os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "OLLAMA_MODEL":      os.getenv("OLLAMA_MODEL", "gemma3"),
            "CLOUD_PROVIDER":    os.getenv("CLOUD_PROVIDER", "gemini").lower(),
            "GEMINI_API_KEY":    os.getenv("GEMINI_API_KEY", ""),
            "GEMINI_MODEL":      os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            "OPENAI_API_KEY":    os.getenv("OPENAI_API_KEY", ""),
            "OPENAI_MODEL":      os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "LLM_MODE":          os.getenv("LLM_MODE", "auto").lower(),
            "TIMEZONE":          os.getenv("TIMEZONE", platform_manager.get_system_timezone()),
            "NOTES_DIR":         os.getenv("NOTES_DIR", str(paths_manager.notes_dir)),
            "FILES_DIR":         os.getenv("FILES_DIR", str(paths_manager.files_dir)),
            "MAX_SEARCH_RESULTS": os.getenv("MAX_SEARCH_RESULTS", "5"),
            "HTTP_TIMEOUT_SEC":  os.getenv("HTTP_TIMEOUT_SEC", "10"),
            "POLLING_INTERVAL_MS": os.getenv("POLLING_INTERVAL_MS", "2000"),
            "GOOGLE_API_KEY":    os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", "")),
            "GOOGLE_SEARCH_ENABLED": os.getenv("GOOGLE_SEARCH_ENABLED", "false").lower(),
            "GOOGLE_SEARCH_REGION":  os.getenv("GOOGLE_SEARCH_REGION", "IN"),
            "GOOGLE_SEARCH_LANGUAGE": os.getenv("GOOGLE_SEARCH_LANGUAGE", "en"),
            "TAVILY_API_KEY":    os.getenv("TAVILY_API_KEY", ""),
            "TAVILY_SEARCH_ENABLED": os.getenv("TAVILY_SEARCH_ENABLED", "true").lower(),
            "COMMERCE_SEARCH_PROVIDER": os.getenv("COMMERCE_SEARCH_PROVIDER", "tavily").lower(),
        }

        # Validate Cloud Key Availability & Mode Switching
        mode = self._config["LLM_MODE"]
        cloud_provider = self._config["CLOUD_PROVIDER"]
        has_gemini = bool(self._config["GEMINI_API_KEY"] and not self._config["GEMINI_API_KEY"].startswith("your_"))
        has_openai = bool(self._config["OPENAI_API_KEY"] and not self._config["OPENAI_API_KEY"].startswith("your_"))

        if mode in ("online", "auto"):
            if cloud_provider == "gemini" and not has_gemini:
                log.warning("Gemini API key missing/invalid. Automatically switching LLM_MODE to Local (offline).")
                self._config["LLM_MODE"] = "offline"
            elif cloud_provider == "gpt" and not has_openai:
                log.warning("OpenAI API key missing/invalid. Automatically switching LLM_MODE to Local (offline).")
                self._config["LLM_MODE"] = "offline"

    def get(self, key: str, default: str = "") -> str:
        return self._config.get(key, os.getenv(key, default))

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self.get(key, str(default)))
        except ValueError:
            return default

    def mask_secret(self, secret: str) -> str:
        if not secret or len(secret) < 8:
            return "******"
        return f"{secret[:4]}...{secret[-4:]}"

    def get_masked_config(self) -> dict[str, str]:
        """Return a copy of config with secrets masked for safe log output."""
        safe_copy = dict(self._config)
        for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "TAVILY_API_KEY"):
            if safe_copy.get(k):
                safe_copy[k] = self.mask_secret(safe_copy[k])
        return safe_copy


environment_manager = EnvironmentManager()
