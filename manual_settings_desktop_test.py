"""
manual_settings_desktop_test.py — Real Manual Windows Settings Test Flow
==========================================================================
Verifies Test A:
1. "Open Settings"
2. "Search for Display"
3. "Open Display settings"
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("helios.test.settings")

def run_settings_flow():
    from agent import HELIOSAgent

    agent = HELIOSAgent()
    session_mgr = agent.session_manager

    steps = [
        "Open Settings",
        "Search for Display",
        "Open Display settings",
        "Stop session"
    ]

    log.info("=======================================================")
    log.info("STARTING MANUAL WINDOWS SETTINGS DESKTOP AUTOMATION FLOW")
    log.info("=======================================================")

    for i, step in enumerate(steps, 1):
        log.info(f"\n--- [Step {i}] Instruction: '{step}' ---")
        response = agent.process(step)
        ctx = session_mgr.get_current_context()
        obs = session_mgr.observer
        target_hwnd, target_title, target_app = obs.get_target_window_info()

        log.info(f"[Step {i}] HELIOS Response:\n{response}")
        log.info(f"-> Target App: {target_app} | Window: '{target_title}' (HWND: {target_hwnd})")
        log.info(f"-> HELIOS Window Excluded: {not obs.is_helios_window(target_hwnd, target_title, target_app)}")
        log.info(f"-> Session State: {ctx.session_state.value}")

    log.info("=======================================================")
    log.info("WINDOWS SETTINGS DESKTOP AUTOMATION FLOW COMPLETED")
    log.info("=======================================================")

if __name__ == "__main__":
    run_settings_flow()
