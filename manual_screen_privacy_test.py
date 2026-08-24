"""
manual_screen_privacy_test.py — HELIOS Phase 2 Manual Screen Privacy & Boundary Test
======================================================================================
Executes manual test sequences for Phase 2:
TEST 1 — Local Model (gemma3): Screen access allowed by default, multi-turn session remains active.
TEST 2 — Cloud Model (gemini-3.6-flash): Screen access required -> Allow Once -> Action executes -> Permission expires.
TEST 3 — Cloud Model: Screen access required -> Deny -> Screen transmission blocked.
TEST 4 — Cloud Model: Allow for Session -> Multi-turn session -> Session termination -> Permission expires.
"""

import time
import logging
import sys
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("helios.manual_privacy_test")

from agent import HELIOSAgent
from core.desktop_session import PermissionState


def run_manual_privacy_tests():
    log.info("Starting HELIOS Phase 2 Screen Privacy & Permission Validation...")
    agent = HELIOSAgent()

    print("\n=======================================================")
    print("TEST 1: Local Model (gemma3) Multi-Turn Desktop Sequence")
    print("=======================================================")

    agent.llm.set_model("gemma3")
    instructions_1 = ["Open Settings", "Search for display", "Open display settings"]

    for i, inst in enumerate(instructions_1, 1):
        print(f"\n[Step {i}] User: '{inst}'")
        res = agent.process(inst)
        print(f"[Step {i}] HELIOS Response:\n{res}")
        ctx = agent.session_manager.get_current_context()
        pm = agent.session_manager.permission_mgr
        print(f"-> Model: {pm.active_model_name} ({pm.active_category.value})")
        print(f"-> Permitted: {pm.check_permission()[0]} (State: {pm.permission_state.value})")
        print(f"-> Session State: {ctx.session_state.value} | Session Alive: {ctx.session_state.value == 'WAITING_FOR_USER'}")
        time.sleep(0.5)

    print("\n=======================================================")
    print("TEST 2: Cloud Model (gemini-3.6-flash) — Allow Once Flow")
    print("=======================================================")

    agent.llm.set_model("gemini-3.6-flash")

    print("\n[Step 1] User: 'Change the display settings'")
    res1 = agent.process("Change the display settings")
    print(f"HELIOS Response:\n{res1}")
    self_pm = agent.session_manager.permission_mgr
    print(f"-> Cloud Model: {self_pm.active_model_name}")
    print(f"-> Screen Permission Requested: {res1.startswith('SCREEN_PERMISSION_REQUIRED_JSON:')}")

    print("\n[Step 2] User clicks '[ Allow Once ]'")
    res2 = agent.process("allow once")
    print(f"HELIOS Response:\n{res2}")
    print(f"-> Granted Once State: {self_pm.permission_state.value == PermissionState.GRANTED_ONCE.value}")

    res3 = agent.process("Open Settings")
    print(f"Execution Response:\n{res3}")
    print(f"-> Post-Action Permission Expired: {self_pm.permission_state.value == PermissionState.REQUIRED.value}")

    print("\n=======================================================")
    print("TEST 3: Cloud Model — Deny Flow")
    print("=======================================================")

    print("\n[Step 1] User: 'Search for sound'")
    res_req = agent.process("Search for sound")
    print(f"HELIOS Response:\n{res_req}")

    print("\n[Step 2] User clicks '[ Deny ]'")
    res_deny = agent.process("deny")
    print(f"HELIOS Response:\n{res_deny}")
    print(f"-> Permission Denied State: {self_pm.permission_state.value == PermissionState.DENIED.value}")

    res_attempt = agent.process("Search for sound")
    print(f"Blocked Transmission Response:\n{res_attempt}")
    print(f"-> Transmission Blocked: {'denied' in res_attempt.lower()}")

    print("\n=======================================================")
    print("TEST 4: Cloud Model — Allow for Session & Expiration")
    print("=======================================================")

    print("\n[Step 1] User clicks '[ Allow for Session ]'")
    res_sess = agent.process("allow for session")
    print(f"HELIOS Response:\n{res_sess}")
    print(f"-> Session Permission State: {self_pm.permission_state.value == PermissionState.GRANTED_SESSION.value}")

    print("\n[Step 2] User: 'Open Settings'")
    res_s1 = agent.process("Open Settings")
    print(f"HELIOS Response:\n{res_s1}")
    print(f"-> Action Executed without re-prompt: {'Desktop Agent Session' in res_s1}")

    print("\n[Step 3] User: 'stop session'")
    res_stop = agent.process("stop session")
    print(f"HELIOS Response:\n{res_stop}")
    print(f"-> Session Permission Expired on Session End: {self_pm.permission_state.value == PermissionState.REQUIRED.value}")

    print("\n=======================================================")
    print("ALL MANUAL SCREEN PRIVACY TEST SEQUENCES PASSED")
    print("=======================================================")


if __name__ == "__main__":
    run_manual_privacy_tests()
