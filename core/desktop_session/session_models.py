"""
core/desktop_session/session_models.py — Data Models for Desktop Session
========================================================================
Defines session states, screen observation structures, semantic actions, goals, semantic targets, and session context.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time
import uuid


class DesktopSessionState(str, Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    OBSERVING = "OBSERVING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class ScreenElement:
    text: str
    element_type: str = "button"  # button, input, text, window, link
    bounds: Optional[List[int]] = None  # [x, y, width, height]
    identifier: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "element_type": self.element_type,
            "bounds": self.bounds,
            "identifier": self.identifier,
        }


@dataclass
class ScreenState:
    timestamp: float = field(default_factory=time.time)
    active_window_title: str = "Desktop"
    active_app_name: str = "explorer.exe"
    screenshot_path: Optional[str] = None
    ocr_text: str = ""
    ui_elements: List[ScreenElement] = field(default_factory=list)
    screen_summary: str = "Desktop visible"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "active_window_title": self.active_window_title,
            "active_app_name": self.active_app_name,
            "screenshot_path": self.screenshot_path,
            "ocr_text": self.ocr_text,
            "ui_elements": [e.to_dict() for e in self.ui_elements],
            "screen_summary": self.screen_summary,
        }


@dataclass
class SemanticTarget:
    target_type: str  # SEARCH_RESULT, BUTTON, TEXT_INPUT, LINK, PRODUCT_CARD
    index: int = 1
    label: str = ""
    identifier: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_type": self.target_type,
            "index": self.index,
            "label": self.label,
            "identifier": self.identifier,
        }


@dataclass
class DesktopAction:
    action_type: str  # OPEN_APPLICATION, NAVIGATE, CLICK, TYPE, KEYPRESS, SCROLL, WAIT_FOR_TRANSITION, VERIFY_GOAL, WINDOW_CONTROL, TERMINATE
    target: str = ""
    value: str = ""
    expected_state: str = ""
    raw_command: str = ""
    target_app: str = ""      # e.g. "chrome", "settings", "notepad", "helios"
    target_url: str = ""      # e.g. "https://www.amazon.in/"
    target_element: str = ""  # e.g. "search_box", "btn_add_to_cart"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "target": self.target,
            "value": self.value,
            "expected_state": self.expected_state,
            "raw_command": self.raw_command,
            "target_app": self.target_app,
            "target_url": self.target_url,
            "target_element": self.target_element,
        }


@dataclass
class DesktopGoal:
    goal_type: str  # SEARCH, NAVIGATE, OPEN_APPLICATION, SELECT_ITEM, ADD_TO_CART, PAY, CUSTOM, TERMINATE
    target_app: str = "chrome"
    target_site: str = ""
    query: str = ""
    completion_condition: str = ""  # SEARCH_RESULTS_VISIBLE, PAGE_READY, APP_OPENED, ITEM_SELECTED, CART_UPDATED
    semantic_target: Optional[SemanticTarget] = None
    action_plan: List[DesktopAction] = field(default_factory=list)
    raw_instruction: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_type": self.goal_type,
            "target_app": self.target_app,
            "target_site": self.target_site,
            "query": self.query,
            "completion_condition": self.completion_condition,
            "semantic_target": self.semantic_target.to_dict() if self.semantic_target else None,
            "action_plan": [a.to_dict() for a in self.action_plan],
            "raw_instruction": self.raw_instruction,
        }


@dataclass
class FocusResult:
    success: bool
    hwnd: int = 0
    process: str = ""
    window_title: str = ""
    foreground_verified: bool = False
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "hwnd": self.hwnd,
            "process": self.process,
            "window_title": self.window_title,
            "foreground_verified": self.foreground_verified,
            "error_message": self.error_message,
        }


@dataclass
class ActionResult:
    success: bool
    observed_state: Optional[ScreenState] = None
    verification_passed: bool = False
    verification_reason: str = ""
    error_message: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "observed_state": self.observed_state.to_dict() if self.observed_state else None,
            "verification_passed": self.verification_passed,
            "verification_reason": self.verification_reason,
            "error_message": self.error_message,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass
class DesktopSessionContext:
    session_id: str = field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    session_state: DesktopSessionState = DesktopSessionState.IDLE
    active_application: str = "explorer.exe"
    active_window: str = "Desktop"
    current_screen_state: Optional[ScreenState] = None
    current_task: str = ""
    last_user_instruction: str = ""
    current_goal: Optional[DesktopGoal] = None
    last_action: Optional[DesktopAction] = None
    last_action_result: Optional[ActionResult] = None
    previous_relevant_actions: List[Dict[str, Any]] = field(default_factory=list)
    current_task_context: Dict[str, Any] = field(default_factory=dict)
    recovery_attempts: int = 0
    max_recovery_attempts: int = 2
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def update_state(self, new_state: DesktopSessionState) -> None:
        self.session_state = new_state
        self.updated_at = time.time()

    def add_action_history(self, action: DesktopAction, result: ActionResult) -> None:
        self.previous_relevant_actions.append({
            "action": action.to_dict(),
            "result": result.to_dict(),
            "timestamp": time.time(),
        })
        if len(self.previous_relevant_actions) > 20:
            self.previous_relevant_actions = self.previous_relevant_actions[-20:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_state": self.session_state.value,
            "active_application": self.active_application,
            "active_window": self.active_window,
            "current_screen_state": self.current_screen_state.to_dict() if self.current_screen_state else None,
            "current_task": self.current_task,
            "last_user_instruction": self.last_user_instruction,
            "current_goal": self.current_goal.to_dict() if self.current_goal else None,
            "last_action": self.last_action.to_dict() if self.last_action else None,
            "last_action_result": self.last_action_result.to_dict() if self.last_action_result else None,
            "previous_relevant_actions": self.previous_relevant_actions,
            "current_task_context": self.current_task_context,
            "recovery_attempts": self.recovery_attempts,
            "max_recovery_attempts": self.max_recovery_attempts,
        }
