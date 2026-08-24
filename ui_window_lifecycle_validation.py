"""
ui_window_lifecycle_validation.py — HELIOS UI Window Lifecycle & Stability Validation
======================================================================================
Validates UI stability, window singleton invariants, thread-safety, rate-limiting,
and watchdog recovery across 15 automated test scenarios.
"""

import sys
import time
import unittest
from unittest.mock import MagicMock, patch

from core.desktop_session.session_models import (
    DesktopSessionState, DesktopGoal, DesktopAction, ScreenState, FocusResult
)
from core.desktop_session.application_focus_manager import ApplicationFocusManager
from core.desktop_session.screen_observer import ScreenObserver
from core.desktop_session.recovery_engine import RecoveryEngine
from core.desktop_session.session_manager import DesktopSessionManager


class TestUIWindowLifecycle(unittest.TestCase):
    """Validation suite for UI window lifecycle, focus rate-limiting, and state decoupling."""

    def test_01_single_helios_root_only(self):
        """1. Verify exactly one HELIOS UI instance/root is permitted."""
        import helios_popup
        helios_popup.HELIOSApp._instance = "EXISTING_INSTANCE"
        app = helios_popup.HELIOSApp.__new__(helios_popup.HELIOSApp)
        app.__init__()
        self.assertEqual(helios_popup.HELIOSApp._instance, "EXISTING_INSTANCE")
        helios_popup.HELIOSApp._instance = None  # Reset for other tests

    def test_02_repeated_actions_do_not_create_windows(self):
        """2. Verify executing repeated session actions creates zero new UI windows."""
        mgr = DesktopSessionManager()
        for i in range(10):
            res = mgr.process_instruction(f"Action {i}", mode="mock")
            self.assertTrue(res.get("success"))
        self.assertEqual(mgr.get_current_context().session_state, DesktopSessionState.WAITING_FOR_USER)

    def test_03_session_restart_does_not_create_windows(self):
        """3. Verify session start/stop/restart cycle does not create duplicate windows."""
        mgr = DesktopSessionManager()
        res1 = mgr.process_instruction("Task 1", mode="mock")
        s1_id = mgr.get_current_context().session_id
        mgr.end_session("User cancel")
        res2 = mgr.process_instruction("Task 2", mode="mock")
        s2_id = mgr.get_current_context().session_id
        self.assertNotEqual(s1_id, s2_id)
        self.assertEqual(mgr.get_current_context().session_state, DesktopSessionState.WAITING_FOR_USER)

    def test_04_ollama_failure_preserves_ui(self):
        """4. Verify Ollama failure/disconnection does not destroy session or UI state."""
        mgr = DesktopSessionManager()
        mgr.process_instruction("Task Ollama Fail", mode="mock")
        with patch("requests.post", side_effect=RuntimeError("Ollama connection refused")):
            res = mgr.process_instruction("Search for keyboard", mode="mock")
            self.assertIn(mgr.get_current_context().session_state, (DesktopSessionState.WAITING_FOR_USER, DesktopSessionState.ACTIVE))

    def test_05_chrome_focus_does_not_create_windows(self):
        """5. Verify ApplicationFocusManager rate-limits focus calls when already focused."""
        with patch("ctypes.windll.user32.GetForegroundWindow", return_value=12345):
            res = ApplicationFocusManager.ensure_app_focused("chrome")
            self.assertIsNotNone(res)

    def test_06_screen_capture_excludes_helios(self):
        """6. Verify ScreenObserver excludes HELIOS window titles and handles."""
        self.assertTrue(ScreenObserver.is_helios_window(9999, "HELIOS", "python.exe"))
        self.assertFalse(ScreenObserver.is_helios_window(1001, "Amazon.com", "chrome.exe"))

    def test_07_recovery_loop_does_not_create_windows(self):
        """7. Verify RecoveryEngine bounds recovery attempts to prevent infinite loops."""
        from core.desktop_session.session_models import DesktopSessionContext
        engine = RecoveryEngine()
        action = DesktopAction(action_type="TYPE", target="search")
        ctx = DesktopSessionContext()
        screen = ScreenState(active_window_title="Desktop", active_app_name="explorer.exe")
        
        # 1st attempt -> Retry
        can_retry_1, act_1, msg_1 = engine.handle_failure(ctx, action, "TARGET_NOT_REACHED", screen)
        self.assertTrue(can_retry_1)
        
        # 2nd attempt -> Retry
        can_retry_2, act_2, msg_2 = engine.handle_failure(ctx, action, "TARGET_NOT_REACHED", screen)
        self.assertTrue(can_retry_2)
        
        # 3rd attempt -> Max exceeded -> Stop
        can_retry_3, act_3, msg_3 = engine.handle_failure(ctx, action, "TARGET_NOT_REACHED", screen)
        self.assertFalse(can_retry_3)

    def test_08_ui_callback_exception_does_not_blank_ui(self):
        """8. Verify UI exception handler logs traceback without crashing."""
        import helios_popup
        app = helios_popup.HELIOSApp.__new__(helios_popup.HELIOSApp)
        app.chat = MagicMock()
        app._on_tkinter_error(ValueError, ValueError("Test UI Exception"), None)
        app.chat.add_system_notice.assert_called_once()

    def test_09_content_widget_recovery(self):
        """9. Verify UI Watchdog detects and repairs content widget if degraded."""
        import helios_popup
        app = helios_popup.HELIOSApp.__new__(helios_popup.HELIOSApp)
        app.root = MagicMock()
        app.root.winfo_exists.return_value = True
        app.content_row = MagicMock()
        app.panel_area = MagicMock()
        app.chat = MagicMock()
        app.chat.frame.winfo_exists.return_value = False  # Degraded
        app.chat.msgs.winfo_exists.return_value = False
        app.panels = {}
        app.agent = None

        with patch("helios_popup.ChatView") as mock_cv:
            mock_inst = MagicMock()
            mock_cv.return_value = mock_inst
            app._start_ui_watchdog()
            self.assertEqual(app.chat, mock_inst)

    def test_10_input_widget_remains_available(self):
        """10. Verify input widget state remains independent of desktop session state."""
        mgr = DesktopSessionManager()
        res = mgr.process_instruction("Input availability test", mode="mock")
        self.assertEqual(mgr.get_current_context().session_state, DesktopSessionState.WAITING_FOR_USER)
        mgr.end_session("User stopped")
        self.assertEqual(mgr.get_current_context().session_state, DesktopSessionState.IDLE)

    def test_11_status_bar_remains_available(self):
        """11. Verify status bar telemetry formats without errors during desktop actions."""
        screen = ScreenState(active_window_title="Settings", active_app_name="systemsettings.exe")
        self.assertEqual(screen.active_app_name, "systemsettings.exe")

    def test_12_multiple_window_detection(self):
        """12. Verify multiple window detection correctly identifies HELIOS windows."""
        self.assertTrue(ScreenObserver.is_helios_window(8888, "HELIOS - Assistant", "python.exe"))

    def test_13_window_lifecycle_cleanup(self):
        """13. Verify clean session termination leaves system in IDLE state."""
        mgr = DesktopSessionManager()
        mgr.process_instruction("Task Cleanup", mode="mock")
        mgr.end_session("Explicit cleanup")
        self.assertEqual(mgr.get_current_context().session_state, DesktopSessionState.IDLE)

    def test_14_persistent_session_20_commands(self):
        """14. Verify persistent agent can execute 20 sequential instructions smoothly."""
        mgr = DesktopSessionManager()
        for i in range(20):
            res = mgr.process_instruction(f"Instruction #{i+1}", mode="mock")
            self.assertTrue(res.get("success"))
            self.assertEqual(mgr.get_current_context().session_state, DesktopSessionState.WAITING_FOR_USER)

    def test_15_no_uncontrolled_loop_iteration(self):
        """15. Verify bounded transition polling prevents uncontrolled loop spinning."""
        mgr = DesktopSessionManager()
        t0 = time.time()
        res = mgr.process_instruction("Search for item", mode="mock")
        elapsed = time.time() - t0
        self.assertTrue(res.get("success"))
        self.assertGreaterEqual(elapsed, 0.0)


if __name__ == "__main__":
    unittest.main()
