"""
scratch/capture_all_acceptance_screenshots.py
Captures all 7 required real desktop screenshots for HELIOS visual material refinement acceptance testing.
"""
import subprocess
import time
import pyautogui
from pathlib import Path

ARTIFACTS_DIR = Path(r"C:\Users\bhara\.gemini\antigravity-ide\brain\22ab8b8c-badf-4072-bd9c-a535534346f3")
PYTHON_EXE = Path(r"d:\HELIOS_FINAL\HELIOS_FINAL\venv\Scripts\python.exe")
CWD = Path(r"d:\HELIOS_FINAL\HELIOS_FINAL")

STEPS = [
    ("launch",   "stepA_launch.png"),
    ("hello",    "stepC_hello.png"),
    ("thinking", "stepE_thinking.png"),
    ("working",  "stepG_working.png"),
    ("response", "stepI_response.png"),
    ("activity", "stepK_activity.png"),
    ("all",      "stepM_chat_return.png"),
]

def run_acceptance_sequence():
    for mode, filename in STEPS:
        print(f"--- Launching mode: {mode} ---")
        proc = subprocess.Popen([str(PYTHON_EXE), "ui_visual_prototype.py", "--mode", mode], cwd=str(CWD))
        time.sleep(3)
        shot = pyautogui.screenshot()
        out_path = ARTIFACTS_DIR / filename
        shot.save(out_path)
        print(f"Saved {filename} to {out_path}")
        proc.terminate()
        proc.wait(timeout=3)
        time.sleep(1)

if __name__ == "__main__":
    run_acceptance_sequence()
    print("ALL 7 ACCEPTANCE SCREENSHOTS CAPTURED SUCCESSFULLY!")
