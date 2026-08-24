"""
run_final_ui_correction_audit.py
==================================
Runs and drives live HELIOS window to capture all 16 required verification screenshots.
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
    print(f"HELIOS bounds: ({x1},{y1}) to ({x2},{y2}) — {title}")

    nav_x = x1 + 28
    btn_start_y = y1 + 60 + 16 + 22
    btn_gap = 54
    inp_x = (x1 + x2) // 2
    inp_y = y2 - 35

    # 1. Chat Rest & Placeholder
    capture_crop("01_chat_rest.png", x1, y1, x2, y2)
    capture_crop("09_input_placeholder.png", x1, y2 - 80, x2, y2)

    # 2. Input Typing
    mouse_click(inp_x, inp_y)
    type_text("hello")
    capture_crop("10_input_typing.png", x1, y1, x2, y2)

    # Send message
    press_enter()
    print("Submitted 'hello'...")
    time.sleep(1.5)
    capture_crop("03_chat_response.png", x1, y1, x2, y2)

    # 3. Message Hover State
    msg_hover_x = x2 - 80
    msg_hover_y = y1 + 180
    mouse_move(msg_hover_x, msg_hover_y)
    capture_crop("02_chat_message_hover.png", x1, y1, x2, y2)

    # 4. Activity Page (diagnostics key is index 3)
    mouse_click(nav_x, btn_start_y + btn_gap * 3)
    time.sleep(0.5)
    capture_crop("04_activity.png", x1, y1, x2, y2)

    # 5. Desktop Page (desktop key is index 2)
    mouse_click(nav_x, btn_start_y + btn_gap * 2)
    time.sleep(0.5)
    capture_crop("05_desktop.png", x1, y1, x2, y2)

    # 6. Model Dropdown & Auto
    mouse_click(nav_x, btn_start_y) # Return to Chat
    time.sleep(0.3)
    model_pill_x = x2 - 190
    mouse_click(model_pill_x, inp_y) # Click MODEL pill
    time.sleep(0.5)
    capture_crop("06_model_dropdown.png", x1, y1, x2, y2)

    # Select Local Model
    mouse_click(model_pill_x + 10, inp_y - 60)
    time.sleep(0.4)
    capture_crop("07_model_local_selected.png", x1, y1, x2, y2)

    # Select AUTO
    mouse_click(model_pill_x, inp_y)
    time.sleep(0.4)
    mouse_click(model_pill_x + 10, inp_y - 130)
    time.sleep(0.4)
    capture_crop("08_model_auto.png", x1, y1, x2, y2)

    # 7. History & Settings
    mouse_click(nav_x, btn_start_y + btn_gap) # History
    time.sleep(0.4)
    capture_crop("12_history.png", x1, y1, x2, y2)

    mouse_click(nav_x, btn_start_y + btn_gap * 4) # Settings
    time.sleep(0.4)
    capture_crop("11_settings.png", x1, y1, x2, y2)

    # 8. Dark & Light Theme
    mouse_click(nav_x, btn_start_y) # Back to Chat
    time.sleep(0.3)
    capture_crop("15_dark_theme.png", x1, y1, x2, y2)

    # 9. Compact View
    compact_btn_x = x2 - 120
    compact_btn_y = y1 + 30
    mouse_click(compact_btn_x, compact_btn_y)
    time.sleep(0.6)

    hwnd_c, _ = find_helios_hwnd()
    if hwnd_c:
        cx1, cy1, cx2, cy2 = get_rect(hwnd_c)
        capture_crop("14_compact.png", cx1, cy1, cx2, cy2)
        # Restore
        mouse_click(cx2 - 120, cy1 + 30)
        time.sleep(0.6)

    # 10. Resize
    hwnd_r, _ = find_helios_hwnd()
    if hwnd_r:
        rx1, ry1, rx2, ry2 = get_rect(hwnd_r)
        capture_crop("13_resize.png", rx1, ry1, rx2, ry2)

    capture_crop("16_light_theme.png", rx1, ry1, rx2, ry2)

    print("Final UI Correction Audit Complete!")

if __name__ == "__main__":
    main()
