"""
core/desktop_session/session_manager.py — Desktop Session Lifecycle & Goal Execution Engine
=============================================================================================
Manages persistent multi-turn desktop sessions.
Executes semantic DesktopGoals with multi-step action plans, bounded page-transition waiting,
and state verification. Enforces the invariant: Action Completion != Goal Completion.
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple

from .session_models import (
    DesktopSessionState,
    DesktopSessionContext,
    ScreenState,
    DesktopAction,
    DesktopGoal,
    ActionResult,
)
from .screen_observer import ScreenObserver
from .state_verifier import StateVerifier
from .recovery_engine import RecoveryEngine
from .task_continuity import TaskContinuityEngine
from .agent_controller import LocalAgentController
from .screen_permission_manager import ScreenPermissionManager, PermissionState
from .screen_context_builder import ScreenContextBuilder
from .screen_redactor import ScreenRedactor

log = logging.getLogger("helios.desktop_session.manager")


class DesktopSessionManager:
    """Manages active persistent desktop sessions and multi-action goal execution."""

    def __init__(self, desktop=None, sysctrl=None, commerce=None, llm=None):
        self.desktop = desktop
        self.sysctrl = sysctrl
        self.commerce = commerce
        self.llm = llm
        self.context = DesktopSessionContext()
        self.observer = ScreenObserver()
        self.controller = LocalAgentController(llm=llm)
        self.permission_mgr = ScreenPermissionManager()

    def get_current_context(self) -> DesktopSessionContext:
        """Return active desktop session context."""
        return self.context

    def end_session(self, reason: str = "User requested termination") -> Dict[str, Any]:
        """Explicitly end current persistent desktop session."""
        log.info("DesktopSessionManager: Session %s ended: %s", self.context.session_id, reason)
        self.context.update_state(DesktopSessionState.COMPLETED)
        self.permission_mgr.on_session_ended()
        res = {
            "success": True,
            "session_id": self.context.session_id,
            "state": self.context.session_state.value,
            "message": f"Desktop session ended. ({reason})",
            "context": self.context.to_dict(),
        }
        self.context = DesktopSessionContext()
        return res

    def process_instruction(self, user_instruction: str, mode: str = "live") -> Dict[str, Any]:
        """
        Process a user instruction within the persistent desktop session.
        Executes multi-step DesktopGoal action plans and keeps session active in WAITING_FOR_USER.
        """
        clean_inst = user_instruction.strip()
        start_time = time.time()

        # 1. Initialize or Reset IDLE Session
        if self.context.session_state in (DesktopSessionState.IDLE, DesktopSessionState.COMPLETED, DesktopSessionState.FAILED):
            self.context = DesktopSessionContext(current_task=clean_inst)
            self.context.update_state(DesktopSessionState.ACTIVE)
            log.info("DesktopSessionManager: Started new desktop session %s for task '%s'", self.context.session_id, clean_inst)

        log.info(
            "DesktopSessionManager: Processing instruction: '%s' [State: %s]",
            clean_inst, self.context.session_state.value
        )
        self.context.last_user_instruction = clean_inst

        # 2. Check for Explicit Termination ("stop", "exit", "close session")
        if TaskContinuityEngine.is_termination_request(clean_inst):
            return self.end_session("User explicit termination")

        # 3. Observe Current Screen State
        self.context.update_state(DesktopSessionState.OBSERVING)
        pre_screen = self.observer.observe(save_screenshot=(mode != "mock"))
        self.context.current_screen_state = pre_screen
        self.context.active_application = pre_screen.active_app_name
        self.context.active_window = pre_screen.active_window_title

        # 4. Privacy & Permission Check
        is_perm, perm_state, perm_reason = self.permission_mgr.check_permission()
        if not is_perm:
            self.context.update_state(DesktopSessionState.WAITING_FOR_USER)
            return {
                "success": False,
                "session_id": self.context.session_id,
                "state": self.context.session_state.value,
                "message": f"⚠️ Screen access denied: {perm_reason}",
                "context": self.context.to_dict(),
            }

        # 5. Commerce Continuity Check
        if TaskContinuityEngine.is_commerce_instruction(clean_inst) and self.commerce:
            if "pay" in clean_inst.lower() or "checkout" in clean_inst.lower():
                log.info("DesktopSessionManager: Commerce payment instruction detected. Routing to TransactionGuard.")
                comm_res = self.commerce.process_commerce_request(clean_inst, mode=mode)
                self.context.update_state(DesktopSessionState.WAITING_FOR_USER)
                self.permission_mgr.on_action_completed()
                return {
                    "success": comm_res.get("success", False),
                    "session_id": self.context.session_id,
                    "state": self.context.session_state.value,
                    "action_executed": "COMMERCE_TRANSACTION",
                    "verification": "REACHED_TRANSACTION_GUARD",
                    "response": comm_res,
                    "message": comm_res.get("message") or "Commerce instruction processed under TransactionGuard.",
                    "context": self.context.to_dict(),
                }

        # 6. Goal & Action Planning Phase
        self.context.update_state(DesktopSessionState.PLANNING)
        planned_goal = self.controller.plan_goal(clean_inst, pre_screen, self.context)
        self.context.current_goal = planned_goal

        # 7. Goal Execution & Observation Loop
        self.context.update_state(DesktopSessionState.EXECUTING)
        last_action = None
        last_exec_success = True
        last_ver_reason = ""
        overall_verified = True
        curr_screen = pre_screen

        for action in planned_goal.action_plan:
            last_action = action
            log.info("DesktopSessionManager: Executing goal action '%s' (%s)", action.action_type, action.target or action.value)

            if action.action_type == "WAIT_FOR_TRANSITION":
                curr_screen = self._wait_for_page_transition(action.target_app, timeout=4.0, mode=mode)
                self.context.current_screen_state = curr_screen
                continue

            exec_ok, exec_msg = self._execute_desktop_action(action, mode=mode)
            if not exec_ok:
                last_exec_success = False
                last_ver_reason = exec_msg
                overall_verified = False
                break

            # Capture post-action screen state
            self.context.update_state(DesktopSessionState.VERIFYING)
            curr_screen = self.observer.observe(save_screenshot=(mode != "mock"))
            if mode == "mock" and action:
                sim_title = action.expected_state or action.target_url or action.target or pre_screen.active_window_title
                curr_screen.active_window_title = sim_title
                if action.action_type in ("NAVIGATE", "CLICK", "TYPE", "KEYPRESS", "VERIFY_GOAL", "WAIT_FOR_TRANSITION") and action.target_app == "chrome":
                    curr_screen.active_app_name = "chrome.exe"
                elif action.target_app == "settings":
                    curr_screen.active_app_name = "SystemSettings.exe"
                else:
                    curr_screen.active_app_name = f"{sim_title.lower().replace(' ', '')}.exe"
                curr_screen.ocr_text = f"Simulated screen state for {sim_title}"

            self.context.current_screen_state = curr_screen
            self.context.active_application = curr_screen.active_app_name
            self.context.active_window = curr_screen.active_window_title

            verified, ver_reason = StateVerifier.verify(action, pre_screen, curr_screen)
            last_ver_reason = ver_reason

            if not verified:
                # Bounded Recovery Attempt
                can_rec, rec_act, _ = RecoveryEngine.handle_failure(
                    self.context, action, ver_reason, curr_screen
                )
                if can_rec and rec_act and mode == "live":
                    log.info("DesktopSessionManager: Executing recovery action -> %s", rec_act.to_dict())
                    self._execute_desktop_action(rec_act, mode=mode)
                    curr_screen = self.observer.observe(save_screenshot=True)
                    rec_ok, rec_reason = StateVerifier.verify(action, pre_screen, curr_screen)
                    if rec_ok:
                        verified = True
                        last_ver_reason = f"Recovered: {rec_reason}"

            if not verified:
                overall_verified = False
                break

        # 8. Record ActionResult & Session Context Updates
        action_result = ActionResult(
            success=last_exec_success and overall_verified,
            observed_state=curr_screen,
            verification_passed=overall_verified,
            verification_reason=last_ver_reason,
            error_message="" if overall_verified else last_ver_reason,
            elapsed_ms=(time.time() - start_time) * 1000,
        )

        TaskContinuityEngine.update_continuity_context(
            self.context, clean_inst, last_action or planned_goal.action_plan[0], overall_verified
        )
        self.context.last_action = last_action or planned_goal.action_plan[0]
        self.context.last_action_result = action_result
        self.permission_mgr.on_action_completed()

        # KEY INVARIANT: Session remains active and transitions to WAITING_FOR_USER
        self.context.update_state(DesktopSessionState.WAITING_FOR_USER)

        if overall_verified and last_exec_success:
            goal_status = "GOAL_SUCCESS"
            status_prefix = f"Goal '{planned_goal.goal_type}' succeeded ({len(planned_goal.action_plan)} actions)."
        else:
            goal_status = "GOAL_FAILED"
            status_prefix = f"⚠️ Goal '{planned_goal.goal_type}' failed ({len(planned_goal.action_plan)} actions)."

        status_msg = (
            f"{status_prefix} Status: {goal_status}. "
            f"Verification: {last_ver_reason}. HELIOS session active (Waiting for next instruction)."
        )

        return {
            "success": overall_verified and last_exec_success,
            "session_id": self.context.session_id,
            "state": self.context.session_state.value,
            "active_application": self.context.active_application,
            "active_window": self.context.active_window,
            "goal": planned_goal.to_dict(),
            "action_executed": (last_action or planned_goal.action_plan[0]).to_dict(),
            "verification_passed": overall_verified,
            "verification_reason": last_ver_reason,
            "message": status_msg,
            "waiting_for_user": True,
            "context": self.context.to_dict(),
        }

    def _wait_for_page_transition(self, target_app: str = "chrome", timeout: float = 4.0, mode: str = "live") -> ScreenState:
        """Poll screen state every 300ms until screen title/OCR changes or timeout occurs."""
        log.info("DesktopSessionManager: Waiting for screen transition on '%s' (timeout=%.1fs, mode=%s)...", target_app, timeout, mode)
        if mode == "mock":
            return self.observer.observe(save_screenshot=False)

        initial = self.observer.observe(save_screenshot=False)
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(0.3)
            curr = self.observer.observe(save_screenshot=False)
            if curr.active_window_title != initial.active_window_title or len(curr.ocr_text) != len(initial.ocr_text):
                log.info("DesktopSessionManager: Transition detected after %.2fs", time.time() - start)
                return curr
        log.info("DesktopSessionManager: Transition wait timeout reached. Continuing with current screen.")
        return self.observer.observe(save_screenshot=False)

    def _execute_desktop_action(self, action: DesktopAction, mode: str = "live") -> Tuple[bool, str]:
        """Execute action reusing existing HELIOS DesktopAgent & SystemControls."""
        if mode == "mock":
            log.info("DesktopSessionManager: [MOCK EXECUTION] %s -> %s", action.action_type, action.target)
            return True, f"Mock executed {action.action_type}"

        act_type = action.action_type.upper()
        target = action.target
        val = action.value

        log.info("[DESKTOP EXEC] Action: %s | Target: '%s' | Value: '%s'", act_type, target, val)

        try:
            from .application_focus_manager import ApplicationFocusManager
            if act_type in ("TYPE", "CLICK", "KEYPRESS", "NAVIGATE"):
                target_app = action.target_app or "chrome"
                focus_res = ApplicationFocusManager.ensure_app_focused(target_app, self.desktop)
                if not focus_res.success and mode != "mock":
                    log.warning("DesktopSessionManager: Focus failed on target_app '%s': %s", target_app, focus_res.error_message)
                    return False, f"HELIOS could not establish focus on target application '{target_app}': {focus_res.error_message}"

            if act_type == "NAVIGATE":
                target_url = action.target_url or action.target or "https://www.amazon.in/"
                if self.desktop:
                    msg = self.desktop.open_website(target_url)
                    return True, msg
                return True, f"Navigated to {target_url}"

            elif act_type == "OPEN_APPLICATION":
                if self.sysctrl and target.lower() in ("settings", "wifi", "bluetooth", "display", "sound"):
                    msg = self.sysctrl.open_settings(target)
                    return True, msg
                elif self.desktop:
                    msg = self.desktop.open_app(target or val)
                    return True, msg
                else:
                    return True, f"Launched {target}"

            elif act_type == "TYPE":
                if self.desktop:
                    import pyautogui
                    pyautogui.typewrite(val or target, interval=0.05)
                    return True, f"Typed '{val or target}'"
                return True, f"Typed '{val}'"

            elif act_type == "CLICK":
                if self.desktop:
                    import pyautogui
                    pyautogui.click()
                    return True, f"Clicked on {target}"
                return True, f"Clicked {target}"

            elif act_type == "KEYPRESS":
                import pyautogui
                pyautogui.press(val or target or "enter")
                return True, f"Pressed key {val or target}"

            elif act_type == "WINDOW_CONTROL":
                if self.desktop and "close" in target.lower():
                    self.desktop.kill_app(val or "current")
                return True, f"Window control {target}"

            elif act_type in ("WAIT_FOR_TRANSITION", "VERIFY_GOAL"):
                return True, f"Action {act_type} completed."

            return True, f"Action {act_type} executed."
        except Exception as exc:
            log.error("DesktopSessionManager: Action execution error: %s", exc, exc_info=True)
            return False, str(exc)
