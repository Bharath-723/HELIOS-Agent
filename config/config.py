"""
config/config.py — Centralized HELIOS System Configuration Manager
===================================================================
Typed configuration wrapper for environment settings, API keys, limits, and runtime modes.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env file if available
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

log = logging.getLogger("helios.config")


class HELIOSConfig:
    """Centralized configuration object for HELIOS components."""

    def __init__(self, env_override: Optional[Dict[str, str]] = None) -> None:
        env = os.environ if env_override is None else env_override

        # Application Metadata
        self.app_name: str = "HELIOS Autonomous Agent"
        self.version: str = "1.0.0"
        self.environment: str = env.get("HELIOS_ENV", "production").lower().strip()

        # Model Routing & LLM Provider Configuration
        self.default_model: str = env.get("DEFAULT_MODEL", "gemini-3.6-flash").strip()
        self.fallback_model: str = env.get("FALLBACK_MODEL", "openrouter/free").strip()
        self.ollama_base_url: str = env.get("OLLAMA_BASE_URL", "http://localhost:11434").strip()
        self.openrouter_api_key: str = env.get("OPENROUTER_API_KEY", "").strip()
        self.gemini_api_key: str = env.get("GEMINI_API_KEY", "").strip()

        # Razorpay Payment & Security Configuration
        self.razorpay_key_id: str = env.get("RAZORPAY_KEY_ID", "").strip()
        self.razorpay_key_secret: str = env.get("RAZORPAY_KEY_SECRET", "").strip()
        self.razorpay_mode: str = env.get("RAZORPAY_MODE", "sandbox").lower().strip()
        
        try:
            max_amt = float(env.get("MAX_PAYMENT_AMOUNT_INR", "10000"))
            self.max_payment_amount_paise: int = int(max_amt * 100)
        except ValueError:
            self.max_payment_amount_paise = 1000000  # Default ₹10,000

        # Sandbox & Execution Limits
        try:
            self.sandbox_timeout_seconds: float = float(env.get("SANDBOX_TIMEOUT_SECONDS", "15.0"))
        except ValueError:
            self.sandbox_timeout_seconds = 15.0

        # Logging & Observability
        self.log_level: str = env.get("LOG_LEVEL", "INFO").upper().strip()
        self.log_dir: Path = Path(__file__).parent.parent / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_razorpay_live_test_mode(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret and not self.razorpay_key_id.startswith("rzp_test_sandbox"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "app_name": self.app_name,
            "version": self.version,
            "environment": self.environment,
            "default_model": self.default_model,
            "ollama_base_url": self.ollama_base_url,
            "razorpay_mode": self.razorpay_mode,
            "max_payment_amount_inr": self.max_payment_amount_paise / 100.0,
            "sandbox_timeout_seconds": self.sandbox_timeout_seconds,
            "razorpay_credentials_configured": bool(self.razorpay_key_id and self.razorpay_key_secret)
        }


# Singleton global configuration instance
config = HELIOSConfig()
