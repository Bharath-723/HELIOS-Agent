"""
core/desktop_session/recovery_engine.py — Bounded Recovery Engine
=================================================================
Manages bounded recovery attempts when action execution or verification fails.
Enforces MAX_RECOVERY_ATTEMPTS = 2 limit.
"""

import logging
from typing import Tuple, Optional
from .session_models import (
    DesktopSessionContext,
    DesktopSessionState,
    DesktopAction,
    ScreenState,
)

log = logging.getLogger("helios.desktop_session.recovery")


class RecoveryEngine:
    """Handles bounded action failure recovery."""

    MAX_RECOVERY_ATTEMPTS = 2

    @classmethod
    def handle_failure(
        cls,
        context: DesktopSessionContext,
        failed_action: DesktopAction,
        reason: str,
        current_screen: ScreenState
    ) -> Tuple[bool, Optional[DesktopAction], str]:
        """
        Evaluate failure and generate recovery action if within recovery budget.
        Returns:
            (can_recover: bool, recovery_action: Optional[DesktopAction], report_message: str)
        """
        context.recovery_attempts += 1
        log.warning(
            "RecoveryEngine: Action failure detected (%d/%d): %s. Reason: %s",
            context.recovery_attempts,
            cls.MAX_RECOVERY_ATTEMPTS,
            failed_action.action_type if failed_action else "UNKNOWN",
            reason,
        )

        if context.recovery_attempts > cls.MAX_RECOVERY_ATTEMPTS:
            context.update_state(DesktopSessionState.WAITING_FOR_USER)
            msg = (
                f"⚠️ Action '{failed_action.target or failed_action.action_type}' failed verification: {reason}. "
                f"Max recovery limit ({cls.MAX_RECOVERY_ATTEMPTS}) reached. HELIOS is waiting for your next instruction."
            )
            log.error("RecoveryEngine: %s", msg)
            return False, None, msg

        context.update_state(DesktopSessionState.RECOVERING)

        # Generate contextual recovery action
        recovery_action = None
        action_type = (failed_action.action_type or "").upper()
        target = failed_action.target or ""

        if action_type == "OPEN_APPLICATION":
            # Retry opening application
            recovery_action = DesktopAction(
                action_type="OPEN_APPLICATION",
                target=target,
                value="",
                expected_state=failed_action.expected_state,
                raw_command=f"retry open {target}",
            )
        elif action_type in ("CLICK", "TYPE"):
            # Focus window or press Escape/Enter before retry
            recovery_action = DesktopAction(
                action_type="KEYPRESS",
                target="Escape",
                value="escape",
                expected_state=failed_action.expected_state,
                raw_command="press escape to reset state",
            )
        else:
            recovery_action = DesktopAction(
                action_type="KEYPRESS",
                target="Return",
                value="enter",
                expected_state=failed_action.expected_state,
                raw_command="press enter",
            )

        report_msg = (
            f"🔄 Recovery attempt {context.recovery_attempts}/{cls.MAX_RECOVERY_ATTEMPTS}: "
            f"Retrying action to reach '{failed_action.expected_state or failed_action.target}'."
        )
        return True, recovery_action, report_msg
