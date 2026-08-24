"""
scratch/capture_compact_desktop_acceptance.py
========================================
Runs real desktop GUI capture sequence for compact/mobile view acceptance testing.
"""

from __future__ import annotations
import sys
import os
import time
import pyautogui
from pathlib import Path

# Ensure current project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui_visual_prototype import HeliosVisualPrototype

ARTIFACTS_DIR = Path(r"C:\Users\bhara\.gemini\antigravity-ide\brain\22ab8b8c-badf-4072-bd9c-a535534346f3")

def run():
    print("--- 1. Launching HELIOS Prototype in Desktop Mode ---")
    app = HeliosVisualPrototype(mode="all")
    root = app.root

    root.update()
    time.sleep(2)
    pyautogui.screenshot().save(ARTIFACTS_DIR / "compact_stepA_desktop.png")
    print("Saved compact_stepA_desktop.png")

    print("--- 2. Toggling to Compact Mode (420x760) ---")
    app._toggle_compact_mode()
    root.update()
    time.sleep(2)
    pyautogui.screenshot().save(ARTIFACTS_DIR / "compact_stepB_compact.png")
    print("Saved compact_stepB_compact.png")

    print("--- 3. Capturing Chat in Compact View ---")
    root.update()
    time.sleep(2)
    pyautogui.screenshot().save(ARTIFACTS_DIR / "compact_stepC_chat.png")
    print("Saved compact_stepC_chat.png")

    print("--- 4. Showing THINKING State in Compact View ---")
    app.mode = "thinking"
    app._render_feed_mode()
    root.update()
    time.sleep(2)
    pyautogui.screenshot().save(ARTIFACTS_DIR / "compact_stepD_thinking.png")
    print("Saved compact_stepD_thinking.png")

    print("--- 5. Showing WORKING State in Compact View ---")
    app.mode = "working"
    app._render_feed_mode()
    root.update()
    time.sleep(2)
    pyautogui.screenshot().save(ARTIFACTS_DIR / "compact_stepE_working.png")
    print("Saved compact_stepE_working.png")

    print("--- 6. Returning to Desktop View ---")
    app._toggle_compact_mode()
    root.update()
    time.sleep(2)
    pyautogui.screenshot().save(ARTIFACTS_DIR / "compact_stepF_desktop_return.png")
    print("Saved compact_stepF_desktop_return.png")

    root.destroy()
    print("SUCCESS: ALL 6 COMPACT DESKTOP SCREENSHOTS SAVED!")

if __name__ == "__main__":
    run()
