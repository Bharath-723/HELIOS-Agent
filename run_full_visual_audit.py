"""
run_full_visual_audit.py
========================
Automated visual audit capture for HELIOS desktop application.
Captures screenshots for all 15 phases directly from the running Tkinter GUI.
"""

import sys
import time
import subprocess
import ctypes
from pathlib import Path
from PIL import ImageGrab

ROOT = Path(__file__).parent
AUDIT_DIR = ROOT / "scratch" / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

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
            if "HELIOS" in buf.value or "helios" in buf.value.lower():
                found.append(hwnd)
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return found[0] if found else None

def bring_to_front(hwnd):
    user32.ShowWindow(hwnd, 9) # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)

def get_rect(hwnd):
    r = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)

def capture(filename, hwnd=None):
    time.sleep(0.3)
    if hwnd:
        x1, y1, x2, y2 = get_rect(hwnd)
        # Ensure coordinates are non-negative and valid
        x1, y1 = max(0, x1), max(0, y1)
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    else:
        img = ImageGrab.grab()
    path = AUDIT_DIR / filename
    img.save(str(path))
    print(f"Captured {filename}")

def mouse_click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.1)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.2)

def mouse_move(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.1)

def type_string(s):
    for ch in s:
        vk = user32.VkKeyScanW(ord(ch)) & 0xFF
        user32.keybd_event(vk, 0, 0, 0)
        user32.keybd_event(vk, 0, 2, 0)
        time.sleep(0.04)

def press_enter():
    user32.keybd_event(0x0D, 0, 0, 0)
    user32.keybd_event(0x0D, 0, 2, 0)
    time.sleep(0.1)

def main():
    # 2. Launch production app
    py_path = str(ROOT / "venv" / "Scripts" / "python.exe")
    app_path = str(ROOT / "helios_popup.py")
    print("Launching HELIOS...")
    proc = subprocess.Popen([py_path, app_path], cwd=str(ROOT))
    time.sleep(5)

    hwnd = find_helios_hwnd()
    if not hwnd:
        print("Failed to find HELIOS window!")
        capture("01_real_launch_failed.png")
        return

    bring_to_front(hwnd)
    x1, y1, x2, y2 = get_rect(hwnd)
    print(f"HELIOS bounds: {x1}, {y1}, {x2}, {y2}")

    # Phase 1 & 2: Baseline
    capture("01_real_launch.png", hwnd)

    # Phase 3: Nav icons
    # Nav buttons on left rail (width 56px, centered at x1 + 28)
    nav_x = x1 + 28
    start_y = y1 + 60 + 16 + 22 # header + spacer + btn offset
    step_y = 64

    # Nav Rest
    mouse_move(x1 - 50, y1 + 100)
    capture("02_nav_rest_dark.png", hwnd)

    # Nav Hover (Chat)
    mouse_move(nav_x, start_y)
    capture("03_nav_hover_dark.png", hwnd)

    # Nav Pressed (History)
    user32.SetCursorPos(int(nav_x), int(start_y + step_y))
    user32.mouse_event(0x0002, 0, 0, 0, 0) # down
    capture("04_nav_pressed_dark.png", hwnd)
    user32.mouse_event(0x0004, 0, 0, 0, 0) # up

    # Nav Active (Desktop)
    mouse_click(nav_x, start_y + step_y * 2)
    time.sleep(0.3)
    capture("05_nav_active_dark.png", hwnd)

    # Click back to Chat
    mouse_click(nav_x, start_y)
    time.sleep(0.3)

    # Phase 5: Dark Chat Baseline
    capture("10_dark_chat.png", hwnd)

    # Phase 6: Chat Content ("hello")
    # Click input area (bottom center)
    inp_x = (x1 + x2) // 2
    inp_y = y2 - 40
    mouse_click(inp_x, inp_y)
    time.sleep(0.2)
    type_string("hello")
    capture("11_user_message.png", hwnd)
    
    press_enter()
    print("Sent 'hello', waiting for response...")
    capture("13_thinking.png", hwnd)
    time.sleep(2)
    capture("14_working.png", hwnd)
    time.sleep(4)
    capture("12_helios_response.png", hwnd)

    # Phase 8: Input Dock
    mouse_move(x1 - 50, y1 + 100)
    capture("17_input_rest.png", hwnd)
    mouse_move(inp_x, inp_y)
    capture("18_input_hover.png", hwnd)

    # Phase 9: Compact View
    # Toggle compact view in top right of header
    compact_btn_x = x2 - 120
    compact_btn_y = y1 + 30
    mouse_click(compact_btn_x, compact_btn_y)
    time.sleep(0.5)
    
    # Re-find hwnd after geometry change
    hwnd_c = find_helios_hwnd()
    if hwnd_c:
        bring_to_front(hwnd_c)
        capture("20_compact_view.png", hwnd_c)
        # Click toggle again to restore
        cx1, cy1, cx2, cy2 = get_rect(hwnd_c)
        mouse_click(cx2 - 120, cy1 + 30)
        time.sleep(0.5)

    hwnd_r = find_helios_hwnd()
    if hwnd_r:
        bring_to_front(hwnd_r)
        capture("21_desktop_view_restored.png", hwnd_r)

    # Phase 12: Chat visibility check
    # Navigate to Settings and back to Chat
    mouse_click(nav_x, start_y + step_y * 4) # Settings
    time.sleep(0.4)
    mouse_click(nav_x, start_y) # Chat
    time.sleep(0.4)
    capture("26_chat_after_navigation.png", hwnd_r)

    print("Audit run complete!")

if __name__ == "__main__":
    main()
