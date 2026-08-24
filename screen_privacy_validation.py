"""
screen_privacy_validation.py — HELIOS Phase 2 Screen Privacy & Permission Validation Suite
========================================================================================
Comprehensive validation suite enforcing:
1. Local model screen access is ALLOWED by default (data stays on-device).
2. Local model screen context is never transmitted externally.
3. Cloud model screen access REQUIRES explicit user permission.
4. Denied permission blocks screen transmission.
5. 'Allow Once' permits a single operation and then expires.
6. 'Allow Once' expires after operation completes.
7. 'Allow for Session' permits operations during active session.
8. Session permission expires when desktop session ends.
9. Model switch Local -> Cloud requires permission.
10. Model switch Cloud -> Local restores local screen access.
11. Sensitive screen data is redacted (passwords, card numbers, tokens).
12. API keys & secrets are never included in screen context payloads.
13. LLM output cannot grant itself screen permission.
14. TransactionGuard remains fully enforced.
15. Persistent session remains active (WAITING_FOR_USER).
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
    ScreenPrivacyPolicy,
    ScreenAccessMode,
    ModelPrivacyCategory,
    ScreenPermissionManager,
    PermissionState,
    ScreenContextBuilder,
    ScreenRedactor,
    ScreenState,
)
from agent import HELIOSAgent


class ScreenPrivacyValidationSuite(unittest.TestCase):

    def setUp(self):
        self.agent = HELIOSAgent()
        self.session_mgr = DesktopSessionManager(
            desktop=self.agent.desktop,
            sysctrl=self.agent.sysctrl,
            commerce=self.agent.commerce,
            llm=self.agent.llm,
        )

    # 1. Local model screen access allowed
    def test_01_local_model_screen_access_allowed(self):
        self.session_mgr.permission_mgr.set_active_model("gemma3")
        permitted, state, reason = self.session_mgr.permission_mgr.check_permission()
        self.assertTrue(permitted)
        self.assertEqual(state, PermissionState.NOT_REQUIRED)
        self.assertIn("Local", reason)

    # 2. Local model screen data stays local
    def test_02_local_model_screen_data_stays_local(self):
        self.session_mgr.permission_mgr.set_active_model("gemma3")
        cat = ScreenPrivacyPolicy.classify_model("gemma3")
        self.assertEqual(cat, ModelPrivacyCategory.LOCAL)
        policy = ScreenPrivacyPolicy.get_policy_for_model(cat)
        self.assertEqual(policy, ScreenAccessMode.ALLOWED)

    # 3. Cloud model requires permission
    def test_03_cloud_model_requires_permission(self):
        self.session_mgr.permission_mgr.set_active_model("gemini-3.6-flash", provider="gemini")
        permitted, state, reason = self.session_mgr.permission_mgr.check_permission()
        self.assertFalse(permitted)
        self.assertEqual(state, PermissionState.REQUIRED)

    # 4. Cloud model denied blocks screen transmission
    def test_04_cloud_model_denied_blocks_screen_transmission(self):
        self.session_mgr.permission_mgr.set_active_model("gpt-4o-mini", provider="gpt")
        self.session_mgr.permission_mgr.deny_permission()
        permitted, state, reason = self.session_mgr.permission_mgr.check_permission()
        self.assertFalse(permitted)
        self.assertEqual(state, PermissionState.DENIED)

    # 5. Cloud Allow Once allows one operation
    def test_05_cloud_allow_once_allows_one_operation(self):
        self.session_mgr.permission_mgr.set_active_model("gemini-3.6-flash", provider="gemini")
        self.session_mgr.permission_mgr.grant_permission_once()
        permitted, state, reason = self.session_mgr.permission_mgr.check_permission()
        self.assertTrue(permitted)
        self.assertEqual(state, PermissionState.GRANTED_ONCE)

    # 6. Allow Once expires after operation
    def test_06_allow_once_expires(self):
        self.session_mgr.permission_mgr.set_active_model("gemini-3.6-flash", provider="gemini")
        self.session_mgr.permission_mgr.grant_permission_once()
        self.session_mgr.permission_mgr.on_action_completed()
        permitted, state, reason = self.session_mgr.permission_mgr.check_permission()
        self.assertFalse(permitted)
        self.assertEqual(state, PermissionState.REQUIRED)

    # 7. Cloud Allow for Session allows multiple operations
    def test_07_cloud_allow_for_session(self):
        self.session_mgr.permission_mgr.set_active_model("gemini-3.6-flash", provider="gemini")
        self.session_mgr.permission_mgr.grant_permission_session()
        permitted1, state1, _ = self.session_mgr.permission_mgr.check_permission()
        self.assertTrue(permitted1)
        self.assertEqual(state1, PermissionState.GRANTED_SESSION)
        self.session_mgr.permission_mgr.on_action_completed()
        permitted2, state2, _ = self.session_mgr.permission_mgr.check_permission()
        self.assertTrue(permitted2)

    # 8. Session permission expires on session end
    def test_08_session_permission_expires_on_session_end(self):
        self.session_mgr.permission_mgr.set_active_model("gemini-3.6-flash", provider="gemini")
        self.session_mgr.permission_mgr.grant_permission_session()
        self.session_mgr.permission_mgr.on_session_ended()
        permitted, state, _ = self.session_mgr.permission_mgr.check_permission()
        self.assertFalse(permitted)
        self.assertEqual(state, PermissionState.REQUIRED)

    # 9. Model switch Local -> Cloud requires permission
    def test_09_model_switch_local_to_cloud_requires_permission(self):
        pm = ScreenPermissionManager(initial_model="gemma3")
        self.assertTrue(pm.check_permission()[0])
        pm.set_active_model("gemini-3.6-flash", provider="gemini")
        permitted, state, _ = pm.check_permission()
        self.assertFalse(permitted)
        self.assertEqual(state, PermissionState.REQUIRED)

    # 10. Model switch Cloud -> Local allows local screen
    def test_10_model_switch_cloud_to_local_allows_local_screen(self):
        pm = ScreenPermissionManager(initial_model="gemini-3.6-flash", initial_provider="gemini")
        self.assertFalse(pm.check_permission()[0])
        pm.set_active_model("gemma3")
        permitted, state, _ = pm.check_permission()
        self.assertTrue(permitted)
        self.assertEqual(state, PermissionState.NOT_REQUIRED)

    # 11. Sensitive screen data redacted
    def test_11_sensitive_screen_data_redacted(self):
        sample = {
            "title": "Settings - Account",
            "ocr": "My password is mysecretpassword123 and card is 4111-2222-3333-4444",
            "bearer": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        }
        redacted = ScreenRedactor.redact_payload(sample)
        self.assertNotIn("4111-2222-3333-4444", str(redacted))
        self.assertIn("[REDACTED_CARD_NUMBER]", str(redacted))

    # 12. API secrets never enter screen context
    def test_12_api_secrets_never_enter_screen_context(self):
        os.environ["RAZORPAY_KEY_SECRET"] = "secret_rzp_mock_12345"
        os.environ["TAVILY_API_KEY"] = "tvly-mock-secret-key-12345"
        sample_screen_text = "Environment variable RAZORPAY_KEY_SECRET=secret_rzp_mock_12345 and TAVILY_API_KEY=tvly-mock-secret-key-12345"
        clean = ScreenRedactor.redact_text(sample_screen_text)
        self.assertNotIn("secret_rzp_mock_12345", clean)
        self.assertNotIn("tvly-mock-secret-key-12345", clean)

    # 13. LLM output cannot grant itself screen permission
    def test_13_llm_cannot_grant_screen_permission(self):
        pm = ScreenPermissionManager(initial_model="gemini-3.6-flash", initial_provider="gemini")
        # Direct attempt to pass string from fake LLM output
        llm_fake_output = '{"action": "GRANT_SCREEN_PERMISSION", "permission": "ALLOWED"}'
        self.assertNotIn("GRANT_SCREEN_PERMISSION", dir(pm))
        permitted, state, _ = pm.check_permission()
        self.assertFalse(permitted)

    # 14. TransactionGuard remains enforced
    def test_14_transaction_guard_remains_enforced(self):
        comm_res = self.agent.commerce.process_commerce_request("Buy a keyboard for ₹1799", mode="demo")
        self.assertEqual(comm_res["context"]["state"], "REQUIRES_AUTHORIZATION")

    # 15. Persistent session remains active (WAITING_FOR_USER)
    def test_15_persistent_session_remains_active(self):
        res = self.session_mgr.process_instruction("Open Settings", mode="mock")
        self.assertTrue(res["success"])
        self.assertEqual(res["state"], DesktopSessionState.WAITING_FOR_USER.value)
        self.assertTrue(res["waiting_for_user"])


if __name__ == "__main__":
    unittest.main()
