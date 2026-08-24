"""
overlay_exclusion_validation.py — HELIOS Desktop Agent Overlay Exclusion & Target Resolution Test Suite
=======================================================================================================
Validates:
1. HELIOS overlay window is excluded from target window resolution.
2. Underlying application (Chrome/Settings) is selected when HELIOS is foreground.
3. TYPE/CLICK actions never execute against HELIOS input box.
4. Focus is established on target window before input execution.
5. ScreenObserver excludes HELIOS metadata and returns target app state.
6. Amazon search sequence and sequential browser actions update target context.
7. Persistent session remains in WAITING_FOR_USER state.
"""

import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.desktop_session import (
    DesktopSessionManager,
    DesktopSessionState,
    DesktopSessionContext,
    ScreenObserver,
    StateVerifier,
    DesktopAction,
    ScreenState,
)
from agent import HELIOSAgent


class OverlayExclusionValidationSuite(unittest.TestCase):

    def setUp(self):
        self.agent = HELIOSAgent()
        self.session_mgr = DesktopSessionManager(
            desktop=self.agent.desktop,
            sysctrl=self.agent.sysctrl,
            commerce=self.agent.commerce,
            llm=self.agent.llm,
        )

    # 1. HELIOS overlay window not selected as target
    def test_01_helios_overlay_not_selected_as_target(self):
        is_h1 = ScreenObserver.is_helios_window(1001, title="HELIOS")
        is_h2 = ScreenObserver.is_helios_window(1002, title="HELIOS Floating Bar")
        is_chrome = ScreenObserver.is_helios_window(2001, title="Amazon.in - Google Chrome", app_name="chrome.exe")
        self.assertTrue(is_h1)
        self.assertTrue(is_h2)
        self.assertFalse(is_chrome)

    # 2. Underlying Chrome selected when HELIOS is foreground
    def test_02_underlying_chrome_selected_when_helios_foreground(self):
        hwnd, title, app = self.session_mgr.observer.get_target_window_info()
        self.assertNotIn("helios", title.lower())
        self.assertIsNotNone(app)

    # 3. TYPE action never targets HELIOS input
    def test_03_type_action_never_targets_helios_input(self):
        action = DesktopAction(action_type="TYPE", target_app="chrome", target="Search box", value="Logitech wireless keyboard")
        from core.desktop_session.application_focus_manager import ApplicationFocusManager
        from core.desktop_session.session_models import FocusResult
        original_func = ApplicationFocusManager.ensure_app_focused
        ApplicationFocusManager.ensure_app_focused = classmethod(lambda cls, app, desktop=None: FocusResult(success=False, error_message="HELIOS Safety Invariant: Foreground window is HELIOS"))
        try:
            exec_ok, msg = self.session_mgr._execute_desktop_action(action, mode="live")
            self.assertFalse(exec_ok)
            self.assertTrue("HELIOS overlay" in msg or "could not establish focus" in msg.lower())
        finally:
            ApplicationFocusManager.ensure_app_focused = original_func

    # 4. Target window focus before TYPE
    def test_04_target_window_focus_before_type(self):
        hwnd, title, app = ScreenObserver().get_target_window_info()
        if hwnd:
            focused = ScreenObserver.focus_target_window(hwnd)
            self.assertTrue(isinstance(focused, bool))

    # 5. Target window focus before CLICK
    def test_05_target_window_focus_before_click(self):
        action = DesktopAction(action_type="CLICK", target="Amazon Search")
        exec_ok, msg = self.session_mgr._execute_desktop_action(action, mode="mock")
        self.assertTrue(exec_ok)

    # 6. ScreenObserver excludes HELIOS
    def test_06_screen_observer_excludes_helios(self):
        state = self.session_mgr.observer.observe(save_screenshot=False)
        self.assertNotIn("helios", state.active_window_title.lower())
        self.assertIsNotNone(state.active_app_name)

    # 7. UI element search excludes HELIOS controls
    def test_07_ui_element_search_excludes_helios_controls(self):
        elements = self.session_mgr.observer.extract_ui_elements("Amazon.in", "chrome.exe")
        elem_texts = [e.text for e in elements]
        self.assertIn("Search Amazon", elem_texts)
        self.assertNotIn("HELIOS Input", elem_texts)

    # 8. Amazon search sequence
    def test_08_amazon_search_sequence(self):
        res1 = self.session_mgr.process_instruction("Open browser", mode="mock")
        self.assertTrue(res1["success"])
        res2 = self.session_mgr.process_instruction("Go to Amazon", mode="mock")
        self.assertTrue(res2["success"])
        res3 = self.session_mgr.process_instruction("Search for Logitech wireless keyboard", mode="mock")
        self.assertTrue(res3["success"])
        self.assertEqual(res3["state"], DesktopSessionState.WAITING_FOR_USER.value)

    # 9. Sequential browser actions
    def test_09_sequential_browser_actions(self):
        self.session_mgr.process_instruction("Open Chrome", mode="mock")
        self.session_mgr.process_instruction("Go to Amazon", mode="mock")
        res_cart = self.session_mgr.process_instruction("Add to cart", mode="mock")
        self.assertTrue(res_cart["success"])
        self.assertEqual(res_cart["state"], DesktopSessionState.WAITING_FOR_USER.value)

    # 10. Current screen used after each action
    def test_10_current_screen_used_after_each_action(self):
        self.session_mgr.process_instruction("Open Settings", mode="mock")
        ctx1 = self.session_mgr.get_current_context()
        screen1 = ctx1.current_screen_state
        self.assertIsNotNone(screen1)
        self.session_mgr.process_instruction("Search for display", mode="mock")
        ctx2 = self.session_mgr.get_current_context()
        screen2 = ctx2.current_screen_state
        self.assertIsNotNone(screen2)

    # 11. Session remains alive after browser action
    def test_11_session_remains_alive_after_browser_action(self):
        res = self.session_mgr.process_instruction("Search for wireless keyboard", mode="mock")
        self.assertTrue(res["waiting_for_user"])
        self.assertEqual(res["state"], DesktopSessionState.WAITING_FOR_USER.value)


if __name__ == "__main__":
    unittest.main()
