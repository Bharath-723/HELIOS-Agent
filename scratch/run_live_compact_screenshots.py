"""
scratch/run_live_compact_screenshots.py
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

from helios_popup import HELIOSApp

ARTIFACTS_DIR = Path(r"C:\Users\bhara\.gemini\antigravity-ide\brain\22ab8b8c-badf-4072-bd9c-a535534346f3")

def run():
    print("--- 1. Launching HELIOS in Desktop Mode ---")
    app = HELIOSApp()
    root = app.root
    root.update()
    time.sleep(2)
    pyautogui.screenshot().save(ARTIFACTS_DIR / "compact_stepA_desktop.png")
    print("Saved compact_stepA_desktop.png")

    print("--- 2. Toggling Compact Mode ---")
    app._toggle_compact_mode()
    root.update()
    time.sleep(2)
    pyautogui.screenshot().save(ARTIFACTS_DIR / "compact_stepB_compact.png")
    print("Saved compact_stepB_compact.png")

    print("--- 3. Inserting Chat Messages ---")
    app.chat.add_user_message("Search for display settings")
    app.chat.add_helios_message("Found 2 display resolution options in Windows Settings.", model_tag="Gemma 3 4B")
    root.update()
    time.sleep(2)
    pyautogui.screenshot().save(ARTIFACTS_DIR / "compact_stepC_chat.png")
    print("Saved compact_stepC_chat.png")

    print("--- 4. Showing THINKING State ---")
    app.chat.show_thinking("Analyzing display parameters...")
    root.update()
    time.sleep(2)
    pyautogui.screenshot().save(ARTIFACTS_DIR / "compact_stepD_thinking.png")
    print("Saved compact_stepD_thinking.png")

    print("--- 5. Showing WORKING State ---")
    app.chat.show_working("Opening Settings → Display...")
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
