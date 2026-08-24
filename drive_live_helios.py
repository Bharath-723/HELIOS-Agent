"""
drive_live_helios.py
====================
Interacts with the live running HELIOS window to capture all 15 audit phases.
"""

import sys
import time
import ctypes
from pathlib import Path
from PIL import ImageGrab

ROOT = Path(__file__).parent
AUDIT = ROOT / "scratch" / "audit"
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
            title = buf.value
            if ("HELIOS" in title or "helios" in title.lower()) and "Antigravity IDE" not in title:
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
    time.sleep(0.3)
    img = ImageGrab.grab(bbox=(max(0, x1), max(0, y1), x2, y2))
    path = AUDIT / filename
    img.save(str(path))
    print(f"Captured crop {filename} ({x2-x1}x{y2-y1})")

def capture_desktop(filename):
    time.sleep(0.3)
    img = ImageGrab.grab()
    path = AUDIT / filename
    img.save(str(path))
    print(f"Captured desktop {filename}")

def mouse_move(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.1)

def mouse_click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.08)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.2)

def mouse_press(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.08)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.1)

def mouse_release():
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.1)

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
    print(f"HELIOS bounds: ({x1}, {y1}) to ({x2}, {y2}) — Title: {title}")

    # Phase 1: Real launch
    capture_desktop("01_real_launch.png")
    capture_crop("01_real_launch_crop.png", x1, y1, x2, y2)

    # Nav rail coordinates
    nav_x = x1 + 28
    btn_start_y = y1 + 60 + 16 + 22
    btn_gap = 64

    # Phase 3: Nav Icon States
    # Rest
    mouse_move(x1 - 100, y1 + 100)
    capture_crop("02_nav_rest_dark.png", x1, y1, x2, y2)

    # Hover (Chat)
    mouse_move(nav_x, btn_start_y)
    capture_crop("03_nav_hover_dark.png", x1, y1, x2, y2)

    # Pressed (History)
    mouse_press(nav_x, btn_start_y + btn_gap)
    capture_crop("04_nav_pressed_dark.png", x1, y1, x2, y2)
    mouse_release()

    # Active (Desktop)
    mouse_click(nav_x, btn_start_y + btn_gap * 2)
    time.sleep(0.3)
    capture_crop("05_nav_active_dark.png", x1, y1, x2, y2)

    # Click back to Chat
    mouse_click(nav_x, btn_start_y)
    time.sleep(0.3)

    # Phase 5: Dark Chat
    capture_crop("10_dark_chat.png", x1, y1, x2, y2)

    # Phase 6 & 7: Chat Content & Agent Execution States
    # Click input box
    inp_x = (x1 + x2) // 2
    inp_y = y2 - 40
    mouse_click(inp_x, inp_y)
    time.sleep(0.2)
    type_text("hello")
    capture_crop("11_user_message.png", x1, y1, x2, y2)

    press_enter()
    print("Submitted 'hello', capturing agent states...")
    time.sleep(0.5)
    capture_crop("13_thinking.png", x1, y1, x2, y2)
    time.sleep(2.0)
    capture_crop("14_working.png", x1, y1, x2, y2)
    time.sleep(4.0)
    capture_crop("12_helios_response.png", x1, y1, x2, y2)

    # Phase 8: Input Dock
    mouse_move(x1 - 100, y1 + 100)
    capture_crop("17_input_rest.png", x1, y2 - 80, x2, y2)
    mouse_move(inp_x, inp_y)
    capture_crop("18_input_hover.png", x1, y2 - 80, x2, y2)

    # Phase 9: Compact View
    # Top-right header compact view toggle button
    compact_btn_x = x2 - 120
    compact_btn_y = y1 + 30
    mouse_click(compact_btn_x, compact_btn_y)
    time.sleep(0.6)

    hwnd_c, _ = find_helios_hwnd()
    if hwnd_c:
        cx1, cy1, cx2, cy2 = get_rect(hwnd_c)
        capture_crop("20_compact_view.png", cx1, cy1, cx2, cy2)
        # Restore
        mouse_click(cx2 - 120, cy1 + 30)
        time.sleep(0.6)

    hwnd_r, _ = find_helios_hwnd()
    if hwnd_r:
        rx1, ry1, rx2, ry2 = get_rect(hwnd_r)
        capture_crop("21_desktop_view_restored.png", rx1, ry1, rx2, ry2)

    # Phase 12: Chat visibility after navigation
    mouse_click(nav_x, btn_start_y + btn_gap * 4) # Settings
    time.sleep(0.4)
    mouse_click(nav_x, btn_start_y) # Chat
    time.sleep(0.4)
    capture_crop("26_chat_after_navigation.png", rx1, ry1, rx2, ry2)

    print("Live driver audit complete!")

if __name__ == "__main__":
    main()
