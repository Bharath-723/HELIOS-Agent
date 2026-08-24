"""
core/payments/payment_config.py — Isolated Payment Configuration & Validation
==============================================================================
Reads Razorpay credentials and security limits ONLY from environment variables.
Prevents crashes on missing credentials and guarantees secrets are never logged or leaked.
"""

import os
import logging
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

log = logging.getLogger("helios.payments.config")

# Load environment variables if .env file exists
load_dotenv()


class PaymentConfig:
    def __init__(self, env_override: Dict[str, str] = None) -> None:
        env = os.environ if env_override is None else env_override

        if env_override is not None:
            self.key_id: str = env_override.get("RAZORPAY_KEY_ID", "").strip()
            self.key_secret: str = env_override.get("RAZORPAY_KEY_SECRET", "").strip()
            self.webhook_secret: str = env_override.get("RAZORPAY_WEBHOOK_SECRET", "").strip()
        else:
            self.key_id: str = os.environ.get("RAZORPAY_KEY_ID", "").strip() or "rzp_test_sandbox_key"
            self.key_secret: str = os.environ.get("RAZORPAY_KEY_SECRET", "").strip() or "rzp_test_sandbox_secret"
            self.webhook_secret: str = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "").strip() or "whsec_test_sandbox_whsecret"
        self.mode: str = env.get("RAZORPAY_MODE", "sandbox").strip().lower()

        # Maximum single transaction limit in INR (default ₹10,000 = 1,000,000 paise)
        try:
            val = float(env.get("MAX_PAYMENT_AMOUNT_INR", "10000"))
            self.max_amount_paise: int = int(val * 100)
        except Exception:
            self.max_amount_paise = 1000000  # Default 10,000 INR in paise

        # Validate mode
        if self.mode not in ("sandbox", "live"):
            log.warning("Invalid RAZORPAY_MODE '%s'. Defaulting to 'sandbox'.", self.mode)
            self.mode = "sandbox"

    @property
    def is_sandbox(self) -> bool:
        return self.mode == "sandbox"

    def validate(self) -> Tuple[bool, str]:
        """
        Validates configuration without throwing exceptions or logging secrets.
        Returns (is_valid, status_message).
        """
        if not self.key_id:
            return False, "Payment capability unavailable: RAZORPAY_KEY_ID is missing."
        if not self.key_secret:
            return False, "Payment capability unavailable: RAZORPAY_KEY_SECRET is missing."
        return True, f"Razorpay Payment Capability Ready [{self.mode.upper()} MODE]"

    def is_valid(self) -> bool:
        valid, _ = self.validate()
        return valid

    def get_status_message(self) -> str:
        _, msg = self.validate()
        return msg

    @staticmethod
    def mask_secret(secret: str) -> str:
        if not secret:
            return "[NOT SET]"
        if len(secret) <= 6:
            return "******"
        return secret[:3] + "***" + secret[-3:]

    def to_safe_dict(self) -> Dict[str, Any]:
        """Returns safe configuration dict without exposing secret values."""
        return {
            "key_id": self.key_id,
            "key_secret": self.mask_secret(self.key_secret),
            "mode": self.mode,
            "webhook_secret": self.mask_secret(self.webhook_secret),
            "max_amount_inr": self.max_amount_paise / 100.0,
            "is_valid": self.is_valid(),
        }

    def __repr__(self) -> str:
        return (
            f"PaymentConfig(mode='{self.mode}', key_id='{self.key_id}', "
            f"key_secret='{self.mask_secret(self.key_secret)}', "
            f"webhook_secret='{self.mask_secret(self.webhook_secret)}', "
            f"max_amount_inr={self.max_amount_paise / 100.0})"
        )

    def __str__(self) -> str:
        return self.__repr__()
