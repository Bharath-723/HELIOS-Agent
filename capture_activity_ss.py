"""
capture_activity_ss.py
======================
Clicks the Activity icon on the HELIOS Navigation Rail and captures a full screenshot of the Activity page.
"""

import sys
import time
import ctypes
from pathlib import Path
from PIL import ImageGrab

ROOT = Path(__file__).parent
AUDIT = ROOT / "scratch" / "audit_activity"
AUDIT.mkdir(parents=True, exist_ok=True)

user32 = ctypes.windll.user32

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

def find_helios_hwnd():
    found = []
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, 512)
            title = buf.value.strip()
            if ("HELIOS" in title or "helios" in title.lower()) and "Antigravity IDE" not in title and "Google Chrome" not in title and "Visual Studio Code" not in title:
                found.append((hwnd, title))
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return found[0] if found else (None, None)

def get_rect(hwnd):
    r = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom

def mouse_click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.08)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.3)

def main():
    hwnd, title = find_helios_hwnd()
    if not hwnd:
        print("HELIOS window not found!")
        return

    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)

    x1, y1, x2, y2 = get_rect(hwnd)
    print(f"HELIOS window found: ({x1},{y1}) to ({x2},{y2}) — {title}")

    # Navigation Rail icon coordinates
    # Nav rail starts below header (60px) + top padding (16px)
    # Item 0 (Chat): y1 + 60 + 16 + 22 = y1 + 98
    # Item 1 (History): + 54 = y1 + 152
    # Item 2 (Desktop): + 54 = y1 + 206
    # Item 3 (Activity/Diagnostics): + 54 = y1 + 260
    nav_x = x1 + 28
    
    # Click Desktop (Item 2)
    print("Clicking Desktop icon...")
    mouse_click(nav_x, y1 + 206)
    time.sleep(0.5)
    
    # Click Activity (Item 3)
    print("Clicking Activity icon...")
    mouse_click(nav_x, y1 + 260)
    time.sleep(1.0)

    # Capture Activity page screenshot
    x1, y1, x2, y2 = get_rect(hwnd)
    img = ImageGrab.grab(bbox=(max(0, x1), max(0, y1), x2, y2))
    ss_path = AUDIT / "activity_page_screenshot.png"
    img.save(str(ss_path))
    print(f"Saved Activity screenshot to {ss_path}")

if __name__ == "__main__":
    main()
