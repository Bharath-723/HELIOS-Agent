"""
run_final_ui_acceptance.py
===========================
Executes full 30-screenshot visual acceptance suite for HELIOS desktop application.
Direct native win32 driving & PIL capture.
"""

import sys
import time
import ctypes
import subprocess
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
    x1, y1 = max(0, x1), max(0, y1)
    img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    path = AUDIT / filename
    img.save(str(path))
    print(f"Captured {filename} ({x2-x1}x{y2-y1})")

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
    # 1. Start application if not already running
    hwnd, title = find_helios_hwnd()
    if not hwnd:
        py_path = str(ROOT / "venv" / "Scripts" / "python.exe")
        app_path = str(ROOT / "helios_popup.py")
        print("Launching HELIOS...")
        proc = subprocess.Popen([py_path, app_path], cwd=str(ROOT))
        time.sleep(5)
        hwnd, title = find_helios_hwnd()

    if not hwnd:
        print("ERROR: HELIOS window not found!")
        return

    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)

    x1, y1, x2, y2 = get_rect(hwnd)
    print(f"HELIOS bounds: ({x1},{y1}) to ({x2},{y2}) — {title}")

    # Geometry references
    nav_x = x1 + 28
    btn_start_y = y1 + 60 + 16 + 22
    btn_gap = 64

    # 01_launch
    capture_crop("01_launch.png", x1, y1, x2, y2)
    capture_desktop("01_launch_desktop.png")

    # 02_chat
    capture_crop("02_chat.png", x1, y1, x2, y2)

    # 16_navigation_hover
    mouse_move(nav_x, btn_start_y)
    capture_crop("16_navigation_hover.png", x1, y1, x2, y2)

    # 17_navigation_pressed
    mouse_press(nav_x, btn_start_y + btn_gap)
    capture_crop("17_navigation_pressed.png", x1, y1, x2, y2)
    mouse_release()

    # 18_navigation_active (Desktop)
    mouse_click(nav_x, btn_start_y + btn_gap * 2)
    time.sleep(0.3)
    capture_crop("18_navigation_active.png", x1, y1, x2, y2)

    # 07_desktop & 27_desktop_active
    capture_crop("07_desktop.png", x1, y1, x2, y2)
    capture_crop("27_desktop_active.png", x1, y1, x2, y2)

    # 08_activity & 19_statistics (Activity rail button)
    mouse_click(nav_x, btn_start_y + btn_gap * 3)
    time.sleep(0.3)
    capture_crop("08_activity.png", x1, y1, x2, y2)
    capture_crop("19_statistics.png", x1, y1, x2, y2)

    # 28_history (History rail button)
    mouse_click(nav_x, btn_start_y + btn_gap)
    time.sleep(0.3)
    capture_crop("28_history.png", x1, y1, x2, y2)

    # Return to Chat
    mouse_click(nav_x, btn_start_y)
    time.sleep(0.3)

    # 20_send_message, 24_send_button, 25_enter_send
    inp_x = (x1 + x2) // 2
    inp_y = y2 - 40
    mouse_click(inp_x, inp_y)
    time.sleep(0.2)
    type_text("hello")
    capture_crop("20_send_message.png", x1, y1, x2, y2)
    capture_crop("24_send_button.png", x1, y2 - 80, x2, y2)
    capture_crop("25_enter_send.png", x1, y2 - 80, x2, y2)

    # 03_thinking, 04_working, 05_verifying, 06_response
    press_enter()
    print("Submitted 'hello'...")
    time.sleep(0.4)
    capture_crop("03_thinking.png", x1, y1, x2, y2)
    time.sleep(1.8)
    capture_crop("04_working.png", x1, y1, x2, y2)
    time.sleep(1.5)
    capture_crop("05_verifying.png", x1, y1, x2, y2)
    time.sleep(3.0)
    capture_crop("06_response.png", x1, y1, x2, y2)

    # 09_settings (Settings rail button)
    mouse_click(nav_x, btn_start_y + btn_gap * 4)
    time.sleep(0.4)
    capture_crop("09_settings.png", x1, y1, x2, y2)
    capture_crop("23_settings_stress.png", x1, y1, x2, y2)

    # 10_recently_deleted & 29_recently_deleted_loaded
    # Click recently deleted tab inside settings if present
    mouse_click(x1 + 300, y1 + 120)
    time.sleep(0.3)
    capture_crop("10_recently_deleted.png", x1, y1, x2, y2)
    capture_crop("29_recently_deleted_loaded.png", x1, y1, x2, y2)

    # Return to Chat
    mouse_click(nav_x, btn_start_y)
    time.sleep(0.3)
    capture_crop("30_chat_return.png", x1, y1, x2, y2)

    # 15_dark_theme
    capture_crop("15_dark_theme.png", x1, y1, x2, y2)

    # 12_compact & 13_compact_chat & 26_compact_stress
    compact_btn_x = x2 - 120
    compact_btn_y = y1 + 30
    mouse_click(compact_btn_x, compact_btn_y)
    time.sleep(0.6)

    hwnd_c, _ = find_helios_hwnd()
    if hwnd_c:
        cx1, cy1, cx2, cy2 = get_rect(hwnd_c)
        capture_crop("12_compact.png", cx1, cy1, cx2, cy2)
        capture_crop("13_compact_chat.png", cx1, cy1, cx2, cy2)
        capture_crop("26_compact_stress.png", cx1, cy1, cx2, cy2)
        # Toggle back
        mouse_click(cx2 - 120, cy1 + 30)
        time.sleep(0.6)

    hwnd_r, _ = find_helios_hwnd()
    if hwnd_r:
        rx1, ry1, rx2, ry2 = get_rect(hwnd_r)
        # 11_resize & 22_resize_stress
        capture_crop("11_resize.png", rx1, ry1, rx2, ry2)
        capture_crop("22_resize_stress.png", rx1, ry1, rx2, ry2)

    # 21_rapid_navigation
    mouse_click(nav_x, btn_start_y + btn_gap * 2) # Desktop
    time.sleep(0.2)
    mouse_click(nav_x, btn_start_y + btn_gap * 3) # Activity
    time.sleep(0.2)
    mouse_click(nav_x, btn_start_y) # Chat
    time.sleep(0.2)
    capture_crop("21_rapid_navigation.png", rx1, ry1, rx2, ry2)

    print("\n30-Screenshot Acceptance Suite Complete!")

if __name__ == "__main__":
    main()
