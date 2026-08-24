"""
core/desktop_session/screen_privacy_policy.py — Screen Access & Privacy Policy
=============================================================================
Defines privacy access modes, model classification, and screen access policies.
Local models have screen access by default (data stays on-device).
Cloud models require explicit user permission before screen data leaves the device.
"""

import logging
from enum import Enum
from typing import Optional

log = logging.getLogger("helios.desktop_session.privacy_policy")


class ScreenAccessMode(str, Enum):
    LOCAL_ONLY = "local_only"
    ASK = "ask"
    ALLOWED = "allowed"
    DENIED = "denied"


class ModelPrivacyCategory(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"


class ScreenPrivacyPolicy:
    """Policy rules governing desktop screen access based on active model category."""

    LOCAL_SCREEN_ACCESS: ScreenAccessMode = ScreenAccessMode.ALLOWED
    CLOUD_SCREEN_ACCESS: ScreenAccessMode = ScreenAccessMode.ASK

    @classmethod
    def classify_model(cls, model_name: str, provider: Optional[str] = None) -> ModelPrivacyCategory:
        """
        Classify whether a model operates locally or via a cloud API.
        Never infers local for known cloud model signatures.
        """
        name_clean = (model_name or "").lower().strip()
        prov_clean = (provider or "").lower().strip()

        # Known cloud providers & models
        cloud_signatures = ("gemini", "gpt", "openai", "claude", "anthropic", "azure")
        if any(sig in name_clean or sig in prov_clean for sig in cloud_signatures):
            return ModelPrivacyCategory.CLOUD

        # Explicit local signatures
        local_signatures = ("gemma", "mistral", "llama", "ollama", "local", "gguf", "phi", "qwen")
        if any(sig in name_clean or sig in prov_clean for sig in local_signatures):
            return ModelPrivacyCategory.LOCAL

        # Default fallback if provider is specified
        if prov_clean in ("gpt", "gemini", "cloud"):
            return ModelPrivacyCategory.CLOUD

        return ModelPrivacyCategory.LOCAL

    @classmethod
    def get_policy_for_model(cls, category: ModelPrivacyCategory) -> ScreenAccessMode:
        """Return the default screen access policy for a model category."""
        if category == ModelPrivacyCategory.LOCAL:
            return cls.LOCAL_SCREEN_ACCESS
        return cls.CLOUD_SCREEN_ACCESS
