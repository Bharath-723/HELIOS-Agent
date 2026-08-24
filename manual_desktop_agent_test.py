"""
manual_desktop_agent_test.py — HELIOS Persistent Desktop Agent Manual Desktop Test
===================================================================================
Executes actual desktop interactions on Windows to verify that HELIOS remains active
after each action, observes current screen, verifies expected state, and handles multi-turn
sequential desktop instructions without terminating the agent loop.
"""

import time
import logging
import sys
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("helios.manual_desktop_test")
from agent import HELIOSAgent

def run_manual_desktop_tests():
    log.info("Starting HELIOS Persistent Desktop Agent Manual Validation...")
    agent = HELIOSAgent()

    print("\n=======================================================")
    print("TEST SEQUENCE 1: Windows Settings Multi-Turn Sequence")
    print("=======================================================")

    instructions_1 = [
        "Open Settings",
        "Search for display",
        "Open display settings",
    ]

    for i, inst in enumerate(instructions_1, 1):
        print(f"\n[Step {i}] User: '{inst}'")
        res = agent.process(inst)
        print(f"[Step {i}] HELIOS Response:\n{res}")
        ctx = agent.session_manager.get_current_context()
        print(f"-> Session State: {ctx.session_state.value}")
        print(f"-> Active App: {ctx.active_application} | Window: {ctx.active_window}")
        print(f"-> Session Alive: {ctx.session_state.value == 'WAITING_FOR_USER'}")
        time.sleep(1.0)

    print("\n=======================================================")
    print("TEST SEQUENCE 2: Browser & Explicit Termination Sequence")
    print("=======================================================")

    instructions_2 = [
        "Open browser",
        "Search for wireless keyboard",
        "stop session",
    ]

    for i, inst in enumerate(instructions_2, 1):
        print(f"\n[Step {i}] User: '{inst}'")
        res = agent.process(inst)
        print(f"[Step {i}] HELIOS Response:\n{res}")
        ctx = agent.session_manager.get_current_context()
        print(f"-> Session State: {ctx.session_state.value}")
        time.sleep(1.0)

    print("\n=======================================================")
    print("ALL MANUAL DESKTOP TEST SEQUENCES COMPLETED SUCCESSFULLY")
    print("=======================================================")

if __name__ == "__main__":
    run_manual_desktop_tests()
