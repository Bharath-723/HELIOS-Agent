"""
test_full_desktop_grab.py
"""
import time
import subprocess
import ctypes
from pathlib import Path
from PIL import ImageGrab

ROOT = Path(__file__).parent
AUDIT_DIR = ROOT / "scratch" / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# Launch HELIOS
py_path = str(ROOT / "venv" / "Scripts" / "python.exe")
app_path = str(ROOT / "helios_popup.py")
print("Launching HELIOS...")
proc = subprocess.Popen([py_path, app_path], cwd=str(ROOT))
time.sleep(4)

# Grab full desktop
full_img = ImageGrab.grab()
full_img.save(str(AUDIT_DIR / "FULL_DESKTOP_TEST.png"))
print(f"Full desktop captured: {full_img.size}")

# Clean up
proc.terminate()
