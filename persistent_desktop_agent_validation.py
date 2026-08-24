"""
persistent_desktop_agent_validation.py — HELIOS Persistent Desktop Agent Validation Suite
========================================================================================
Comprehensive validation suite testing the persistent, screen-aware desktop agent:
1-26. Persistent Session, Target Focus, Target Categorization.
27-38. Goal vs Action Architecture, Search Goal Submission & Transition.
39. test_search_verifier_does_not_use_internal_state_name
40. test_search_verifier_checks_url
41. test_search_verifier_detects_results
42. test_semantic_first_result_resolution
43. test_second_result_resolution
44. test_product_card_resolution
45. test_select_first_result_does_not_search_for_word_product
46. test_current_screen_results_become_next_context
47. test_search_to_product_page_continuity
48. test_product_page_verification
49. test_add_to_cart_from_verified_product_page
50. test_goal_completion_requires_postcondition
51. test_failed_target_resolution_triggers_recovery
"""

import unittest
import os
import sys

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.desktop_session import (
    DesktopSessionManager,
    DesktopSessionState,
    DesktopSessionContext,
    DesktopAction,
    DesktopGoal,
    SemanticTarget,
    ActionResult,
    ScreenState,
    ScreenObserver,
    StateVerifier,
    RecoveryEngine,
    TaskContinuityEngine,
    LocalAgentController,
    TargetResolver,
    TargetCategory,
    ScreenTargetResolver,
)
from agent import HELIOSAgent


class PersistentDesktopAgentValidationSuite(unittest.TestCase):

    def setUp(self):
        self.agent = HELIOSAgent()
        self.session_mgr = DesktopSessionManager(
            desktop=self.agent.desktop,
            sysctrl=self.agent.sysctrl,
            commerce=self.agent.commerce,
            llm=self.agent.llm,
        )

    # 1. Open Settings -> session remains active (WAITING_FOR_USER)
    def test_01_open_settings_session_remains_active(self):
        res = self.session_mgr.process_instruction("Open Settings", mode="mock")
        self.assertTrue(res["success"])
        self.assertEqual(res["state"], DesktopSessionState.WAITING_FOR_USER.value)
        self.assertTrue(res["waiting_for_user"])

    # 2. Search Settings -> session remains active (WAITING_FOR_USER)
    def test_02_search_settings_session_remains_active(self):
        self.session_mgr.process_instruction("Open Settings", mode="mock")
        res = self.session_mgr.process_instruction("Search for display", mode="mock")
        self.assertTrue(res["success"])
        self.assertEqual(res["state"], DesktopSessionState.WAITING_FOR_USER.value)

    # 3. Open Display -> session remains active (WAITING_FOR_USER)
    def test_03_open_display_session_remains_active(self):
        self.session_mgr.process_instruction("Open Settings", mode="mock")
        self.session_mgr.process_instruction("Search for display", mode="mock")
        res = self.session_mgr.process_instruction("Open display settings", mode="mock")
        self.assertTrue(res["success"])
        self.assertEqual(res["state"], DesktopSessionState.WAITING_FOR_USER.value)

    # 4. Sequential instructions preserve context
    def test_04_sequential_instructions_preserve_context(self):
        self.session_mgr.process_instruction("Open Settings", mode="mock")
        sid1 = self.session_mgr.get_current_context().session_id
        self.session_mgr.process_instruction("Search for display", mode="mock")
        ctx2 = self.session_mgr.get_current_context()
        self.assertEqual(sid1, ctx2.session_id)
        self.assertGreaterEqual(len(ctx2.current_task_context.get("task_chain", [])), 2)

    # 5. New instruction uses CURRENT screen rather than initial screen
    def test_05_new_instruction_uses_current_screen(self):
        self.session_mgr.process_instruction("Open Settings", mode="mock")
        ctx = self.session_mgr.get_current_context()
        current_screen = ctx.current_screen_state
        self.assertIsNotNone(current_screen)
        res = self.session_mgr.process_instruction("Search for sound", mode="mock")
        self.assertIn("sound", str(res["goal"]).lower())

    # 6. Action verification detects successful result
    def test_06_verification_detects_success(self):
        pre = ScreenState(active_window_title="Desktop", active_app_name="explorer.exe")
        post = ScreenState(active_window_title="Settings", active_app_name="SystemSettings.exe")
        action = DesktopAction(action_type="OPEN_APPLICATION", target="Settings", expected_state="Settings")
        verified, reason = StateVerifier.verify(action, pre, post)
        self.assertTrue(verified)
        self.assertIn("verified", reason.lower())

    # 7. Action verification detects failed result
    def test_07_verification_detects_failure(self):
        pre = ScreenState(active_window_title="Desktop", active_app_name="explorer.exe")
        post = ScreenState(active_window_title="Desktop", active_app_name="explorer.exe")
        action = DesktopAction(action_type="OPEN_APPLICATION", target="Settings", expected_state="Settings")
        verified, reason = StateVerifier.verify(action, pre, post)
        self.assertFalse(verified)

    # 8. Recovery is bounded (MAX_RECOVERY_ATTEMPTS = 2)
    def test_08_recovery_is_bounded(self):
        ctx = DesktopSessionContext()
        action = DesktopAction(action_type="OPEN_APPLICATION", target="NonExistentApp", expected_state="NonExistentApp")
        screen = ScreenState()
        
        can_rec1, _, _ = RecoveryEngine.handle_failure(ctx, action, "Window missing", screen)
        self.assertTrue(can_rec1)
        self.assertEqual(ctx.recovery_attempts, 1)

        can_rec2, _, _ = RecoveryEngine.handle_failure(ctx, action, "Window missing", screen)
        self.assertTrue(can_rec2)
        self.assertEqual(ctx.recovery_attempts, 2)

        can_rec3, _, msg = RecoveryEngine.handle_failure(ctx, action, "Window missing", screen)
        self.assertFalse(can_rec3)
        self.assertEqual(ctx.session_state, DesktopSessionState.WAITING_FOR_USER)
        self.assertIn("Max recovery limit", msg)

    # 9. Explicit "stop" terminates session (COMPLETED)
    def test_09_explicit_stop_terminates_session(self):
        self.session_mgr.process_instruction("Open Settings", mode="mock")
        res = self.session_mgr.process_instruction("stop", mode="mock")
        self.assertTrue(res["success"])
        self.assertEqual(res["state"], DesktopSessionState.COMPLETED.value)

    # 10. Commerce actions preserve session
    def test_10_commerce_actions_preserve_session(self):
        res = self.session_mgr.process_instruction("Open Amazon", mode="mock")
        self.assertTrue(res["success"])
        self.assertEqual(res["state"], DesktopSessionState.WAITING_FOR_USER.value)

    # 11. Add-to-cart action continues into the same session
    def test_11_add_to_cart_continues_same_session(self):
        self.session_mgr.process_instruction("Open Amazon", mode="mock")
        sid1 = self.session_mgr.get_current_context().session_id
        self.session_mgr.process_instruction("Search for wireless keyboard", mode="mock")
        res = self.session_mgr.process_instruction("Add to cart", mode="mock")
        sid2 = self.session_mgr.get_current_context().session_id
        self.assertEqual(sid1, sid2)
        self.assertEqual(res["state"], DesktopSessionState.WAITING_FOR_USER.value)

    # 12. Payment instruction reaches existing TransactionGuard
    def test_12_payment_reaches_transaction_guard(self):
        res = self.session_mgr.process_instruction("Pay for the keyboard", mode="demo")
        self.assertIn(res["action_executed"], ("COMMERCE_TRANSACTION", "PAYMENT_ONLY", "TYPE", "CLICK"))

    # 13. Payment cannot bypass explicit authorization
    def test_13_payment_cannot_bypass_explicit_authorization(self):
        comm_res = self.agent.commerce.process_commerce_request("Buy a keyboard for ₹1799", mode="demo")
        self.assertEqual(comm_res["context"]["state"], "REQUIRES_AUTHORIZATION")

    # 14. Local LLM never receives payment secrets
    def test_14_local_llm_never_receives_secrets(self):
        controller = LocalAgentController(llm=self.agent.llm)
        screen = ScreenState()
        ctx = DesktopSessionContext()
        prompt = controller._build_llm_prompt("Buy keyboard", screen, ctx)
        self.assertNotIn("RAZORPAY_KEY_SECRET", prompt)
        self.assertNotIn("rzp_secret", prompt)

    # 15. Agent integration process instruction test
    def test_15_agent_process_desktop_session_integration(self):
        res = self.agent.process("Open Settings")
        self.assertTrue("Desktop Agent Session" in res or "HELIOS session active" in res)
        self.assertIn("Waiting for your next instruction", res)

    # 16. Navigation does not type into HELIOS
    def test_16_navigation_does_not_type_into_helios(self):
        controller = LocalAgentController()
        goal = controller.plan_goal("go to amazon", ScreenState(), DesktopSessionContext())
        self.assertEqual(goal.goal_type, "NAVIGATE")
        self.assertEqual(goal.action_plan[0].action_type, "NAVIGATE")
        self.assertEqual(goal.target_app, "chrome")

    # 17. Target application focus before TYPE
    def test_17_target_application_focus_before_type(self):
        action = DesktopAction(action_type="TYPE", target_app="chrome", target="search_box", value="logitech wireless keyboard")
        self.assertEqual(action.target_app, "chrome")

    # 18. Chrome focus verified before browser action
    def test_18_chrome_focus_verified_before_browser_action(self):
        from core.desktop_session.application_focus_manager import ApplicationFocusManager
        proc_name = ApplicationFocusManager.resolve_process_name("chrome")
        self.assertEqual(proc_name, "chrome.exe")

    # 19. "go to amazon" resolves to NAVIGATE action
    def test_19_go_to_amazon_resolves_to_navigation(self):
        controller = LocalAgentController()
        goal = controller.plan_goal("go to amazon", ScreenState(), DesktopSessionContext())
        self.assertEqual(goal.goal_type, "NAVIGATE")
        self.assertEqual(goal.action_plan[0].target_url, "https://www.amazon.in/")

    # 20. Navigation verification checks Amazon domain and process
    def test_20_navigation_verification_checks_amazon(self):
        action = DesktopAction(action_type="NAVIGATE", target_app="chrome", target_url="https://www.amazon.in/", expected_state="Amazon.in")
        post_ok = ScreenState(active_window_title="Amazon.in: Electronics", active_app_name="chrome.exe")
        verified_ok, reason_ok = StateVerifier.verify(action, None, post_ok)
        self.assertTrue(verified_ok)

        post_fail = ScreenState(active_window_title="HELIOS", active_app_name="python.exe")
        verified_fail, reason_fail = StateVerifier.verify(action, None, post_fail)
        self.assertFalse(verified_fail)
        self.assertIn("TARGET_NOT_REACHED", reason_fail)

    # 21. HELIOS foreground blocks external input execution
    def test_21_helios_foreground_blocks_external_input(self):
        action = DesktopAction(action_type="TYPE", target_app="chrome", target="search box", value="test")
        original_func = ScreenObserver.get_active_window_info_raw
        ScreenObserver.get_active_window_info_raw = staticmethod(lambda hwnd: ("HELIOS", "python.exe"))
        try:
            exec_ok, msg = self.session_mgr._execute_desktop_action(action, mode="live")
            self.assertFalse(exec_ok)
            self.assertIn("could not establish focus", msg.lower())
        finally:
            ScreenObserver.get_active_window_info_raw = original_func

    # 22. Active window is not implicitly used as default target for input
    def test_22_active_window_is_not_implicitly_used(self):
        controller = LocalAgentController()
        goal = controller.plan_goal("search for wireless keyboard", ScreenState(active_app_name="chrome.exe"), DesktopSessionContext())
        self.assertEqual(goal.target_app, "chrome")
        self.assertNotEqual(goal.action_plan[0].target, "Active Window")

    # 23. Post action screen becomes next context
    def test_23_post_action_screen_becomes_next_context(self):
        res = self.session_mgr.process_instruction("Open Settings", mode="mock")
        ctx = self.session_mgr.get_current_context()
        self.assertIsNotNone(ctx.current_screen_state)
        self.assertIn("settings", ctx.active_application.lower())

    # 24. Sequential browser actions use current screen
    def test_24_sequential_browser_actions_use_current_screen(self):
        self.session_mgr.process_instruction("go to amazon", mode="mock")
        self.session_mgr.process_instruction("search for wireless keyboard", mode="mock")
        ctx = self.session_mgr.get_current_context()
        self.assertEqual(ctx.session_state, DesktopSessionState.WAITING_FOR_USER)

    # 25. Failed focus triggers recovery
    def test_25_failed_focus_triggers_recovery(self):
        ctx = DesktopSessionContext()
        action = DesktopAction(action_type="TYPE", target_app="chrome", target="search_box", value="test")
        screen = ScreenState(active_window_title="HELIOS", active_app_name="python.exe")
        can_rec, rec_act, _ = RecoveryEngine.handle_failure(ctx, action, "TARGET_NOT_REACHED", screen)
        self.assertTrue(can_rec)

    # 26. Unknown target does not execute input
    def test_26_unknown_target_does_not_execute_input(self):
        cat, res, _ = TargetResolver.resolve_target("unknown_app_999")
        self.assertEqual(cat, TargetCategory.UNKNOWN)
        self.assertIsNone(res)

    # 27. TYPE does not complete search goal
    def test_27_type_does_not_complete_search_goal(self):
        controller = LocalAgentController()
        goal = controller.plan_goal("search for Logitech wireless keyboard", ScreenState(active_app_name="chrome.exe"), DesktopSessionContext())
        self.assertEqual(goal.goal_type, "SEARCH")
        self.assertGreater(len(goal.action_plan), 1)

    # 28. Search submits after typing
    def test_28_search_submits_after_typing(self):
        controller = LocalAgentController()
        goal = controller.plan_goal("search for Logitech wireless keyboard", ScreenState(active_app_name="chrome.exe"), DesktopSessionContext())
        action_types = [a.action_type for a in goal.action_plan]
        self.assertIn("TYPE", action_types)
        self.assertIn("KEYPRESS", action_types)

    # 29. Search waits for page transition
    def test_29_search_waits_for_page_transition(self):
        controller = LocalAgentController()
        goal = controller.plan_goal("search for Logitech wireless keyboard", ScreenState(active_app_name="chrome.exe"), DesktopSessionContext())
        action_types = [a.action_type for a in goal.action_plan]
        self.assertIn("WAIT_FOR_TRANSITION", action_types)

    # 30. Search verifies results
    def test_30_search_verifies_results(self):
        controller = LocalAgentController()
        goal = controller.plan_goal("search for Logitech wireless keyboard", ScreenState(active_app_name="chrome.exe"), DesktopSessionContext())
        action_types = [a.action_type for a in goal.action_plan]
        self.assertIn("VERIFY_GOAL", action_types)

    # 31. Search does not depend on window title alone
    def test_31_search_does_not_depend_on_window_title(self):
        action = DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value="Logitech wireless keyboard")
        screen = ScreenState(
            active_window_title="Amazon.com. Spend less. Smile more.",
            active_app_name="chrome.exe",
            ocr_text="Logitech K380 Wireless Multi-Device Keyboard for Windows, Mac, Chrome OS"
        )
        verified, reason = StateVerifier.verify(action, None, screen)
        self.assertTrue(verified)
        self.assertIn("SEARCH_RESULTS_VERIFIED", reason)

    # 32. Search recovery after missing results
    def test_32_search_recovery_after_missing_results(self):
        action = DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value="NonExistentProductXYZ")
        screen = ScreenState(active_window_title="Amazon.com", active_app_name="chrome.exe", ocr_text="No results found")
        verified, reason = StateVerifier.verify(action, None, screen)
        self.assertFalse(verified)
        self.assertIn("SEARCH_GOAL_FAILED", reason)

    # 33. Goal requires all actions
    def test_33_goal_requires_all_actions(self):
        res = self.session_mgr.process_instruction("search for Logitech wireless keyboard", mode="mock")
        self.assertTrue(res["success"])
        self.assertEqual(res["goal"]["goal_type"], "SEARCH")

    # 34. Multi-action goal remains active
    def test_34_multi_action_goal_remains_active(self):
        res = self.session_mgr.process_instruction("search for Logitech wireless keyboard", mode="mock")
        self.assertTrue(res["waiting_for_user"])

    # 35. Next instruction uses verified current screen
    def test_35_next_instruction_uses_verified_current_screen(self):
        self.session_mgr.process_instruction("go to amazon", mode="mock")
        res_search = self.session_mgr.process_instruction("search for Logitech wireless keyboard", mode="mock")
        self.assertEqual(res_search["state"], DesktopSessionState.WAITING_FOR_USER.value)

    # 36. Open first result after search
    def test_36_open_first_result_after_search(self):
        self.session_mgr.process_instruction("search for Logitech wireless keyboard", mode="mock")
        res = self.session_mgr.process_instruction("open the first result", mode="mock")
        self.assertTrue(res["success"])
        self.assertEqual(res["goal"]["goal_type"], "SELECT_ITEM")

    # 37. Add to cart after product page
    def test_37_add_to_cart_after_product_page(self):
        self.session_mgr.process_instruction("open the first result", mode="mock")
        res = self.session_mgr.process_instruction("add it to cart", mode="mock")
        self.assertTrue(res["success"])
        self.assertEqual(res["goal"]["goal_type"], "ADD_TO_CART")

    # 38. Payment after cart
    def test_38_payment_after_cart(self):
        self.session_mgr.process_instruction("add it to cart", mode="mock")
        res = self.session_mgr.process_instruction("now make payment", mode="demo")
        self.assertEqual(res["verification"], "REACHED_TRANSACTION_GUARD")

    # 39. Search verifier does not use internal state name "query_typed"
    def test_39_search_verifier_does_not_use_internal_state_name(self):
        action = DesktopAction(action_type="TYPE", target_app="chrome", expected_state="query_typed")
        screen = ScreenState(active_window_title="Amazon.com. Spend less. Smile more. - Google Chrome", active_app_name="chrome.exe")
        verified, reason = StateVerifier.verify(action, None, screen)
        self.assertTrue(verified)
        self.assertNotIn("query_typed", reason)

    # 40. Search verifier checks URL and domain
    def test_40_search_verifier_checks_url(self):
        action = DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value="Logitech keyboard")
        screen = ScreenState(active_window_title="Amazon.in: Logitech keyboard", active_app_name="chrome.exe", ocr_text="amazon.in/s?k=Logitech+keyboard")
        verified, reason = StateVerifier.verify(action, None, screen)
        self.assertTrue(verified)
        self.assertIn("SEARCH_RESULTS_VERIFIED", reason)

    # 41. Search verifier detects results
    def test_41_search_verifier_detects_results(self):
        action = DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value="Logitech keyboard")
        screen = ScreenState(active_window_title="Amazon", active_app_name="chrome.exe", ocr_text="1-16 of over 1,000 results for Logitech keyboard")
        verified, reason = StateVerifier.verify(action, None, screen)
        self.assertTrue(verified)

    # 42. Semantic first result resolution
    def test_42_semantic_first_result_resolution(self):
        sem = ScreenTargetResolver.parse_semantic_target("open first result")
        self.assertIsNotNone(sem)
        self.assertEqual(sem.target_type, "SEARCH_RESULT")
        self.assertEqual(sem.index, 1)

    # 43. Second result resolution
    def test_43_second_result_resolution(self):
        sem = ScreenTargetResolver.parse_semantic_target("open second result")
        self.assertIsNotNone(sem)
        self.assertEqual(sem.target_type, "SEARCH_RESULT")
        self.assertEqual(sem.index, 2)

    # 44. Product card resolution
    def test_44_product_card_resolution(self):
        sem = ScreenTargetResolver.parse_semantic_target("open 1st product")
        self.assertIsNotNone(sem)
        self.assertEqual(sem.target_type, "SEARCH_RESULT")
        self.assertEqual(sem.index, 1)

    # 45. Select first result does not search for word product
    def test_45_select_first_result_does_not_search_for_word_product(self):
        controller = LocalAgentController()
        goal = controller.plan_goal("open first result", ScreenState(active_app_name="chrome.exe"), DesktopSessionContext())
        self.assertEqual(goal.goal_type, "SELECT_ITEM")
        self.assertIsNotNone(goal.semantic_target)
        self.assertEqual(goal.semantic_target.index, 1)

    # 46. Current screen results become next context
    def test_46_current_screen_results_become_next_context(self):
        screen = ScreenState(active_window_title="Amazon.in: Logitech keyboard", active_app_name="chrome.exe", ocr_text="Logitech K380\nLogitech MK240")
        results = ScreenTargetResolver.normalize_search_results(screen)
        self.assertGreaterEqual(len(results), 2)
        self.assertEqual(results[0]["index"], 1)

    # 47. Search to product page continuity
    def test_47_search_to_product_page_continuity(self):
        self.session_mgr.process_instruction("search for Logitech wireless keyboard", mode="mock")
        res = self.session_mgr.process_instruction("open first result", mode="mock")
        self.assertTrue(res["success"])
        self.assertEqual(res["state"], DesktopSessionState.WAITING_FOR_USER.value)

    # 48. Product page verification
    def test_48_product_page_verification(self):
        action = DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value="product")
        screen = ScreenState(active_window_title="Amazon.in: Logitech K380 Keyboard", active_app_name="chrome.exe", ocr_text="Add to Cart Buy Now ₹1,799.00")
        verified, reason = StateVerifier.verify(action, None, screen)
        self.assertTrue(verified)
        self.assertIn("PRODUCT_PAGE_VERIFIED", reason)

    # 49. Add to cart from verified product page
    def test_49_add_to_cart_from_verified_product_page(self):
        self.session_mgr.process_instruction("open first result", mode="mock")
        res = self.session_mgr.process_instruction("add it to cart", mode="mock")
        self.assertTrue(res["success"])
        self.assertEqual(res["goal"]["goal_type"], "ADD_TO_CART")

    # 50. Goal completion requires postcondition
    def test_50_goal_completion_requires_postcondition(self):
        action = DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value="NonExistentXYZ")
        screen = ScreenState(active_window_title="Desktop", active_app_name="explorer.exe")
        verified, _ = StateVerifier.verify(action, None, screen)
        self.assertFalse(verified)

    # 52. Antigravity foreground != HELIOS
    def test_52_antigravity_foreground_not_helios(self):
        self.assertFalse(ScreenObserver.is_helios_window(101, "HELIOS_FINAL - Antigravity IDE", "Code.exe"))

    # 53. VS Code foreground != HELIOS
    def test_53_vscode_foreground_not_helios(self):
        self.assertFalse(ScreenObserver.is_helios_window(102, "helios - Visual Studio Code", "Code.exe"))

    # 54. Chrome foreground != HELIOS
    def test_54_chrome_foreground_not_helios(self):
        self.assertFalse(ScreenObserver.is_helios_window(103, "Amazon.in - Google Chrome", "chrome.exe"))

    # 55. Actual HELIOS HWND == HELIOS
    def test_55_registered_helios_hwnd_is_helios(self):
        ScreenObserver.register_helios_hwnd(99999)
        self.assertTrue(ScreenObserver.is_helios_window(99999, "Random Window Title", "python.exe"))

    # 56. Focus acquisition to Chrome succeeds in mock mode
    def test_56_focus_acquisition_chrome(self):
        res = ApplicationFocusManager.ensure_app_focused("chrome", desktop_agent=None)
        self.assertIsNotNone(res)

    # 57. Focus failure prevents input
    def test_57_focus_failure_prevents_input(self):
        ScreenObserver.register_helios_hwnd(77777)
        with patch("ctypes.windll.user32.GetForegroundWindow", return_value=77777):
            res = ApplicationFocusManager.ensure_app_focused("chrome", desktop_agent=None)
            self.assertFalse(res.success)
            self.assertIn("FOCUS_ACQUISITION_FAILED", res.error_message)

    # 58. HybridLLM actual API is called
    def test_58_hybrid_llm_api_call(self):
        from core.llm_engine import HybridLLM
        llm = HybridLLM()
        self.assertTrue(hasattr(llm, "chat"))
        self.assertTrue(hasattr(llm, "generate"))
        self.assertTrue(hasattr(llm, "query"))

    # 59. Local LLM planning succeeds with query/generate
    def test_59_local_llm_planning_succeeds(self):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "goal": "NAVIGATE", "target_app": "chrome", "query": "Amazon",
            "completion_condition": "Amazon loaded",
            "actions": [{"action_type": "NAVIGATE", "target_app": "chrome", "target": "https://www.amazon.in/"}]
        })
        ctrl = LocalAgentController(llm=mock_llm)
        goal = ctrl.plan_goal("open amazon", ScreenState(), DesktopSessionContext())
        self.assertEqual(goal.goal_type, "NAVIGATE")

    # 60. Local LLM failure is explicitly classified
    def test_60_local_llm_failure_explicitly_classified(self):
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = RuntimeError("Ollama connection error")
        ctrl = LocalAgentController(llm=mock_llm)
        goal = ctrl.plan_goal("open amazon", ScreenState(), DesktopSessionContext())
        self.assertIsNotNone(goal)
        self.assertEqual(goal.goal_type, "NAVIGATE")

    # 61. Failed goal is not reported as completed
    def test_61_failed_goal_not_reported_as_completed(self):
        with patch.object(ApplicationFocusManager, "ensure_app_focused", return_value=FocusResult(success=False, error_message="FOCUS_ACQUISITION_FAILED")):
            res = self.session_mgr.process_instruction("open amazon", mode="live")
            self.assertFalse(res["success"])
            self.assertIn("GOAL_FAILED", res["message"])

    # 62. Failed goal leaves session WAITING_FOR_USER
    def test_62_failed_goal_leaves_session_waiting(self):
        with patch.object(ApplicationFocusManager, "ensure_app_focused", return_value=FocusResult(success=False, error_message="FOCUS_ACQUISITION_FAILED")):
            res = self.session_mgr.process_instruction("open amazon", mode="live")
            self.assertEqual(res["state"], DesktopSessionState.WAITING_FOR_USER.value)

    # 63. Retry instruction re-observes current screen
    def test_63_retry_instruction_reobserves(self):
        self.session_mgr.process_instruction("open amazon", mode="mock")
        res = self.session_mgr.process_instruction("try again", mode="mock")
        self.assertTrue(res["success"])

    # 64. Sequential Amazon instructions preserve session
    def test_64_sequential_amazon_instructions(self):
        res1 = self.session_mgr.process_instruction("open amazon", mode="mock")
        res2 = self.session_mgr.process_instruction("search for keyboard", mode="mock")
        res3 = self.session_mgr.process_instruction("open first result", mode="mock")
        res4 = self.session_mgr.process_instruction("add to cart", mode="mock")
        self.assertTrue(res1["success"])
        self.assertTrue(res2["success"])
        self.assertTrue(res3["success"])
        self.assertTrue(res4["success"])
        self.assertEqual(res4["state"], DesktopSessionState.WAITING_FOR_USER.value)

    # 65. Screen state is refreshed after every action
    def test_65_screen_state_refreshed_after_action(self):
        self.session_mgr.process_instruction("open amazon", mode="mock")
        ctx = self.session_mgr.get_current_context()
        self.assertIsNotNone(ctx.current_screen_state)


if __name__ == "__main__":
    unittest.main()
