"""
core/desktop_session/screen_permission_manager.py — Screen Permission Manager
================================================================================
Independent permission manager enforcing cloud screen privacy boundaries.
Manages permission grants, single-operation / session scoping, model switching, and audit logging.
The LLM can NEVER grant itself screen permission.
"""

import logging
from enum import Enum
from typing import Tuple, Optional, Dict, Any
from .screen_privacy_policy import (
    ScreenPrivacyPolicy,
    ScreenAccessMode,
    ModelPrivacyCategory,
)

log = logging.getLogger("helios.desktop_session.permission")


class PermissionState(str, Enum):
    NOT_REQUIRED = "SCREEN_PERMISSION_NOT_REQUIRED"
    REQUIRED = "SCREEN_PERMISSION_REQUIRED"
    GRANTED_ONCE = "SCREEN_PERMISSION_GRANTED_ONCE"
    GRANTED_SESSION = "SCREEN_PERMISSION_GRANTED_SESSION"
    DENIED = "SCREEN_PERMISSION_DENIED"


class ScreenPermissionManager:
    """Independent Manager for Cloud Screen Permissions."""

    def __init__(self, initial_model: str = "gemma3", initial_provider: Optional[str] = None):
        self.active_model_name: str = initial_model
        self.active_provider: Optional[str] = initial_provider
        self.active_category: ModelPrivacyCategory = ScreenPrivacyPolicy.classify_model(
            initial_model, initial_provider
        )
        self.permission_state: PermissionState = (
            PermissionState.NOT_REQUIRED
            if self.active_category == ModelPrivacyCategory.LOCAL
            else PermissionState.REQUIRED
        )
        self.allow_once_used: bool = False

    def set_active_model(self, model_name: str, provider: Optional[str] = None) -> None:
        """
        Handle active model switching.
        Local -> Cloud: Enforces permission check for cloud.
        Cloud -> Local: Restores local screen access immediately under local policy.
        """
        clean_model = model_name or "gemma3"
        new_category = ScreenPrivacyPolicy.classify_model(clean_model, provider)

        if new_category != self.active_category:
            log.info(
                "[SCREEN PRIVACY] Model switch detected: %s (%s) -> %s (%s)",
                self.active_model_name,
                self.active_category.value,
                clean_model,
                new_category.value,
            )

        self.active_model_name = clean_model
        self.active_provider = provider
        self.active_category = new_category

        if self.active_category == ModelPrivacyCategory.LOCAL:
            self.permission_state = PermissionState.NOT_REQUIRED
            self.allow_once_used = False
            log.info("[SCREEN PRIVACY] model=LOCAL access=ALLOWED transmission=LOCAL_ONLY")
        else:
            # Keep GRANTED_SESSION if already granted for cloud session; otherwise reset to REQUIRED/DENIED
            if self.permission_state not in (
                PermissionState.GRANTED_SESSION,
                PermissionState.DENIED,
            ):
                self.permission_state = PermissionState.REQUIRED
                self.allow_once_used = False

    def check_permission(self) -> Tuple[bool, PermissionState, str]:
        """
        Programmatically check if screen transmission is currently authorized.
        Returns: (is_permitted: bool, state: PermissionState, reason: str)
        """
        if self.active_category == ModelPrivacyCategory.LOCAL:
            log.info("[SCREEN PRIVACY] model=LOCAL access=ALLOWED transmission=LOCAL_ONLY")
            return True, PermissionState.NOT_REQUIRED, "Local model screen access allowed by policy."

        # Cloud Model Checks
        if self.permission_state == PermissionState.GRANTED_SESSION:
            log.info("[SCREEN PRIVACY] model=CLOUD permission=ALLOWED_SESSION transmission=AUTHORIZED")
            return True, PermissionState.GRANTED_SESSION, "Cloud screen access authorized for session."

        if self.permission_state == PermissionState.GRANTED_ONCE:
            if not self.allow_once_used:
                log.info("[SCREEN PRIVACY] model=CLOUD permission=ALLOWED_ONCE transmission=AUTHORIZED")
                return True, PermissionState.GRANTED_ONCE, "Cloud screen access authorized for single operation."
            else:
                self.permission_state = PermissionState.REQUIRED
                log.info("[SCREEN PRIVACY] model=CLOUD permission=EXPIRED transmission=BLOCKED")
                return False, PermissionState.REQUIRED, "Allow once permission expired."

        if self.permission_state == PermissionState.DENIED:
            log.info("[SCREEN PRIVACY] model=CLOUD permission=DENIED transmission=BLOCKED")
            return False, PermissionState.DENIED, "Screen access explicitly denied by user."

        log.info("[SCREEN PRIVACY] model=CLOUD access=REQUIRED transmission=BLOCKED")
        return False, PermissionState.REQUIRED, "Cloud model requires explicit user screen permission."

    def grant_permission_once(self) -> None:
        """User explicitly clicks 'Allow Once'."""
        self.permission_state = PermissionState.GRANTED_ONCE
        self.allow_once_used = False
        log.info("[SCREEN PRIVACY] model=%s permission=ALLOWED_ONCE transmission=AUTHORIZED", self.active_model_name)

    def grant_permission_session(self) -> None:
        """User explicitly clicks 'Allow for Session'."""
        self.permission_state = PermissionState.GRANTED_SESSION
        self.allow_once_used = False
        log.info("[SCREEN PRIVACY] model=%s permission=ALLOWED_SESSION transmission=AUTHORIZED", self.active_model_name)

    def deny_permission(self) -> None:
        """User explicitly clicks 'Deny'."""
        self.permission_state = PermissionState.DENIED
        self.allow_once_used = False
        log.info("[SCREEN PRIVACY] model=%s permission=DENIED transmission=BLOCKED", self.active_model_name)

    def on_action_completed(self) -> None:
        """Called when an operation completes. Expire Allow Once if used."""
        if self.permission_state == PermissionState.GRANTED_ONCE:
            self.allow_once_used = True
            self.permission_state = PermissionState.REQUIRED
            log.info("[SCREEN PRIVACY] model=%s permission=ALLOWED_ONCE_EXPIRED", self.active_model_name)

    def on_session_ended(self) -> None:
        """Expire session permissions when desktop session terminates."""
        log.info("[SCREEN PRIVACY] Desktop session ended. Expiring cloud screen permissions.")
        self.allow_once_used = False
        if self.active_category == ModelPrivacyCategory.CLOUD:
            self.permission_state = PermissionState.REQUIRED
        else:
            self.permission_state = PermissionState.NOT_REQUIRED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_model_name": self.active_model_name,
            "active_provider": self.active_provider,
            "active_category": self.active_category.value,
            "permission_state": self.permission_state.value,
            "allow_once_used": self.allow_once_used,
        }
