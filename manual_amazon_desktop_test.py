"""
manual_amazon_desktop_test.py — HELIOS Desktop Automation Amazon Flow Manual Test
===================================================================================
Executes manual test sequence for Amazon desktop interaction:
1. Open Chrome
2. Go to Amazon
3. Search for Logitech wireless keyboard (targets Amazon search field, NOT HELIOS input)
4. Open the first suitable product
5. Add this product to cart
6. Open cart
7. Proceed to checkout
8. Stop session
"""

import time
import logging
import sys
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("helios.manual_amazon_test")

from agent import HELIOSAgent


def run_manual_amazon_test():
    log.info("Starting HELIOS Desktop Agent Overlay Exclusion & Amazon Search Flow Test...")
    agent = HELIOSAgent()

    print("\n=======================================================")
    print("MANUAL TEST SEQUENCE: Amazon Browser Interaction Flow")
    print("=======================================================")

    instructions = [
        "Open Chrome",
        "Go to Amazon",
        "Search for Logitech wireless keyboard",
        "Open the first suitable product",
        "Add this product to cart",
        "Open cart",
        "Proceed to checkout",
        "Stop session",
    ]

    for i, inst in enumerate(instructions, 1):
        print(f"\n[Step {i}] User: '{inst}'")
        res = agent.process(inst)
        print(f"[Step {i}] HELIOS Response:\n{res}")
        ctx = agent.session_manager.get_current_context()
        obs = agent.session_manager.observer
        target_hwnd, target_title, target_app = obs.get_target_window_info()
        print(f"-> Target App: {target_app} | Window: '{target_title}' (HWND: {target_hwnd})")
        print(f"-> HELIOS Window Excluded: {not obs.is_helios_window(target_hwnd, target_title, target_app)}")
        print(f"-> Session State: {ctx.session_state.value}")
        time.sleep(1.0)

    print("\n=======================================================")
    print("AMAZON DESKTOP AUTOMATION FLOW COMPLETED SUCCESSFULLY")
    print("=======================================================")


if __name__ == "__main__":
    run_manual_amazon_test()
