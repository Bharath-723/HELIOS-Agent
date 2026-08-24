"""
core/desktop_session/screen_redactor.py — Screen Content Redactor
==================================================================
Scans and redacts sensitive information (API keys, secrets, credit cards, tokens)
from screen-derived text before transmission to external context.
"""

import os
import re
import logging
from typing import Dict, Any, Union

log = logging.getLogger("helios.desktop_session.redactor")

# Common sensitive regex patterns
PATTERNS = [
    (r"rzp_(test|live)_[a-zA-Z0-9]{14,24}", "[REDACTED_RAZORPAY_KEY]"),
    (r"tvly-[a-zA-Z0-9_-]{20,50}", "[REDACTED_TAVILY_KEY]"),
    (r"AIzaSy[a-zA-Z0-9_-]{33}", "[REDACTED_GOOGLE_KEY]"),
    (r"sk-[a-zA-Z0-9]{20,50}", "[REDACTED_OPENAI_KEY]"),
    (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "[REDACTED_CARD_NUMBER]"),
    (r"(password|passwd|pwd|secret)\s*[:=]\s*['\"]?[^\s'\"]+['\"]?", "[REDACTED_CREDENTIAL]"),
    (r"Bearer\s+[a-zA-Z0-9\._-]{20,}", "Bearer [REDACTED_TOKEN]"),
]


class ScreenRedactor:
    """Redacts sensitive information from text or dictionary payloads."""

    @classmethod
    def get_known_env_secrets(cls) -> set:
        """Fetch active environment secrets to guarantee zero secret leakage."""
        secrets = set()
        for env_var in (
            "RAZORPAY_KEY_SECRET",
            "RAZORPAY_WEBHOOK_SECRET",
            "TAVILY_API_KEY",
            "GOOGLE_API_KEY",
            "GEMINI_API_KEY",
            "OPENAI_API_KEY",
        ):
            val = os.getenv(env_var, "").strip()
            if val and len(val) > 4:
                secrets.add(val)
        return secrets

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redact known secrets and pattern matches from string input."""
        if not text:
            return ""

        clean = text

        # 1. Exact Environment Secrets Redaction
        for secret in cls.get_known_env_secrets():
            if secret in clean:
                clean = clean.replace(secret, "[REDACTED_ENV_SECRET]")

        # 2. Pattern Matching Redaction
        for pattern, replacement in PATTERNS:
            clean = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)

        return clean

    @classmethod
    def redact_payload(cls, data: Union[Dict[str, Any], list, str]) -> Union[Dict[str, Any], list, str]:
        """Recursively redact dictionary, list, or text payloads."""
        if isinstance(data, str):
            return cls.redact_text(data)
        elif isinstance(data, dict):
            return {k: cls.redact_payload(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.redact_payload(item) for item in data]
        return data
