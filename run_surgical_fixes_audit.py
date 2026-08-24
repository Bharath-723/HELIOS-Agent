"""
run_surgical_fixes_audit.py
==============================
Executes live regression testing for the 4 Surgical Fixes:
  1. InputPanel warning fixes & Camera (📷) button assignment
  2. Activity Panel real runtime telemetry data binding
  3. Desktop Panel vertical scrolling
  4. Responsive text wrapping in compact & narrow modes
"""

import sys
import time
import ctypes
from pathlib import Path
from PIL import ImageGrab

ROOT = Path(__file__).parent
AUDIT = ROOT / "scratch" / "audit_surgical"
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

def capture_crop(filename, x1, y1, x2, y2):
    time.sleep(0.4)
    img = ImageGrab.grab(bbox=(max(0, x1), max(0, y1), x2, y2))
    path = AUDIT / filename
    img.save(str(path))
    print(f"Captured crop {filename} ({x2-x1}x{y2-y1})")

def mouse_click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.08)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.2)

def type_text(text):
    for ch in text:
        vk = user32.VkKeyScanW(ord(ch)) & 0xFF
        user32.keybd_event(vk, 0, 0, 0)
        user32.keybd_event(vk, 0, 2, 0)
        time.sleep(0.04)

def press_enter():
    user32.keybd_event(0x0D, 0, 0, 0)
    user32.keybd_event(0x0D, 0, 2, 0)
    time.sleep(0.1)

def main():
    hwnd, title = find_helios_hwnd()
    if not hwnd:
        print("HELIOS window not found!")
        return

    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)

    x1, y1, x2, y2 = get_rect(hwnd)
    print(f"1. HELIOS window found: ({x1},{y1}) to ({x2},{y2}) — {title}")

    nav_x = x1 + 28
    btn_start_y = y1 + 60 + 16 + 22
    btn_gap = 54
    inp_x = (x1 + x2) // 2
    inp_y = y2 - 35

    # 1. Chat Rest & Zero Warnings Check
    capture_crop("01_chat_zero_warnings.png", x1, y1, x2, y2)

    # 2. Send real request
    mouse_click(inp_x, inp_y)
    type_text("hello")
    press_enter()
    time.sleep(2.5)
    capture_crop("02_chat_response.png", x1, y1, x2, y2)

    # 3. Open Activity - verify real telemetry data
    mouse_click(nav_x, btn_start_y + btn_gap * 3) # Activity tab
    time.sleep(0.6)
    capture_crop("03_activity_real_data.png", x1, y1, x2, y2)

    # 4. Open Desktop - verify scrolling & layout
    mouse_click(nav_x, btn_start_y + btn_gap * 2) # Desktop tab
    time.sleep(0.6)
    capture_crop("04_desktop_scrollable.png", x1, y1, x2, y2)

    # 5. Compact Mode - verify text wrapping
    mouse_click(nav_x, btn_start_y) # Back to Chat
    time.sleep(0.4)
    compact_btn_x = x2 - 120
    compact_btn_y = y1 + 30
    mouse_click(compact_btn_x, compact_btn_y) # Compact view toggle
    time.sleep(0.6)

    hwnd_c, _ = find_helios_hwnd()
    if hwnd_c:
        cx1, cy1, cx2, cy2 = get_rect(hwnd_c)
        capture_crop("05_compact_text_wrapping.png", cx1, cy1, cx2, cy2)
        # Restore full view
        mouse_click(cx2 - 120, cy1 + 30)
        time.sleep(0.6)

    print("Surgical Fixes Audit Complete!")

if __name__ == "__main__":
    main()
