"""
core/desktop_session — HELIOS Persistent Screen-Aware Desktop Agent Subsystem
=============================================================================
"""

from .session_models import (
    DesktopSessionState,
    ScreenElement,
    ScreenState,
    DesktopAction,
    DesktopGoal,
    SemanticTarget,
    ActionResult,
    DesktopSessionContext,
    FocusResult,
)
from .session_manager import DesktopSessionManager
from .screen_observer import ScreenObserver
from .state_verifier import StateVerifier
from .recovery_engine import RecoveryEngine
from .task_continuity import TaskContinuityEngine
from .agent_controller import LocalAgentController
from .application_focus_manager import ApplicationFocusManager
from .screen_target_resolver import ScreenTargetResolver
from .screen_privacy_policy import ScreenPrivacyPolicy, ScreenAccessMode, ModelPrivacyCategory
from .screen_permission_manager import ScreenPermissionManager, PermissionState
from .screen_context_builder import ScreenContextBuilder
from .screen_redactor import ScreenRedactor
from .target_resolver import TargetResolver, TargetCategory

__all__ = [
    "DesktopSessionState",
    "ScreenElement",
    "ScreenState",
    "DesktopAction",
    "DesktopGoal",
    "SemanticTarget",
    "ActionResult",
    "DesktopSessionContext",
    "FocusResult",
    "DesktopSessionManager",
    "ScreenObserver",
    "StateVerifier",
    "RecoveryEngine",
    "TaskContinuityEngine",
    "LocalAgentController",
    "ApplicationFocusManager",
    "ScreenTargetResolver",
    "ScreenPrivacyPolicy",
    "ScreenAccessMode",
    "ModelPrivacyCategory",
    "ScreenPermissionManager",
    "PermissionState",
    "ScreenContextBuilder",
    "ScreenRedactor",
    "TargetResolver",
    "TargetCategory",
]
