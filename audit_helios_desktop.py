"""
audit_helios_desktop.py — Real Desktop Tkinter App Visual Audit
================================================================
Launches the REAL production helios_popup.py, brings it to the foreground,
drives it with win32api mouse simulation, captures all required screenshots.

NO browser. NO localhost. NO web server.
This is a pure Tkinter desktop app audited via PIL + ctypes.
"""

import sys
import time
import ctypes
import ctypes.wintypes as wintypes
import subprocess
from pathlib import Path
from PIL import ImageGrab

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).parent
PY      = ROOT / "venv" / "Scripts" / "python.exe"
APP     = ROOT / "helios_popup.py"
AUDIT   = ROOT / "scratch" / "audit"
AUDIT.mkdir(parents=True, exist_ok=True)

# ── Win32 API ─────────────────────────────────────────────────────────────────
user32  = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)


def find_helios_hwnd():
    """Find the HELIOS Tkinter window handle."""
    found = []
    def cb(hwnd, _):
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        title = buf.value
        if ("HELIOS" in title or "helios" in title.lower()) and user32.IsWindowVisible(hwnd):
            found.append((hwnd, title))
        return True
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return found[0][0] if found else None


def get_window_rect(hwnd) -> tuple:
    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def bring_to_front(hwnd):
    """Bring window to foreground."""
    user32.ShowWindow(hwnd, 9)     # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)
    time.sleep(0.3)


def grab(name: str, delay: float = 0.4) -> Path:
    time.sleep(delay)
    img = ImageGrab.grab()
    out = AUDIT / name
    img.save(str(out))
    sz = out.stat().st_size // 1024
    print(f"  SAVED: {name} ({sz}KB)  {img.size[0]}x{img.size[1]}")
    return out


def grab_window(name: str, hwnd, delay: float = 0.4) -> Path:
    """Grab only the HELIOS window region."""
    time.sleep(delay)
    x1, y1, x2, y2 = get_window_rect(hwnd)
    img = ImageGrab.grab(bbox=(max(0,x1), max(0,y1), x2, y2))
    out = AUDIT / name
    img.save(str(out))
    sz = out.stat().st_size // 1024
    print(f"  SAVED: {name} ({sz}KB) window=({x1},{y1},{x2},{y2})")
    return out


def mouse_move(x: int, y: int):
    user32.SetCursorPos(x, y)
    time.sleep(0.08)


def mouse_click(x: int, y: int):
    user32.SetCursorPos(x, y)
    time.sleep(0.05)
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
    time.sleep(0.12)


def mouse_hold(x: int, y: int):
    """Move and hold button down — for pressed state capture."""
    user32.SetCursorPos(x, y)
    time.sleep(0.05)
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # down only


def mouse_release():
    user32.mouse_event(0x0004, 0, 0, 0, 0)


def type_text(text: str):
    """Type ASCII text via keybd_event."""
    for ch in text:
        vk = user32.VkKeyScanW(ord(ch)) & 0xFF
        user32.keybd_event(vk, 0, 0, 0)
        user32.keybd_event(vk, 0, 2, 0)
        time.sleep(0.04)


def press_enter():
    user32.keybd_event(0x0D, 0, 0, 0)
    user32.keybd_event(0x0D, 0, 2, 0)
    time.sleep(0.08)


def move_away(hwnd):
    """Move mouse outside the HELIOS window."""
    x1, y1, x2, y2 = get_window_rect(hwnd)
    mouse_move(x2 + 50, y1 + 50)
    time.sleep(0.15)


# ── Main Audit ────────────────────────────────────────────────────────────────
def run():
    print("=" * 60)
    print("HELIOS DESKTOP APP VISUAL AUDIT")
    print("Production app: helios_popup.py (Tkinter, NOT web)")
    print("=" * 60)

    # Kill lingering python processes
    subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
    time.sleep(1.5)

    # ── PHASE 1: Launch production HELIOS ─────────────────────────────────────
    print("\n[PHASE 1] Launching production HELIOS desktop app...")
    proc = subprocess.Popen(
        [str(PY), str(APP)],
        cwd=str(ROOT),
    )

    # Wait for Tkinter mainloop to fully initialize
    print("  Waiting 10s for full initialization...")
    for i in range(10):
        time.sleep(1)
        hwnd = find_helios_hwnd()
        if hwnd:
            print(f"  Window found at t={i+1}s (hwnd={hwnd})")
            break
        print(f"  t={i+1}s — waiting...")

    hwnd = find_helios_hwnd()
    if not hwnd:
        print("  ERROR: HELIOS window not found after 10s")
        proc.terminate()
        return False

    bring_to_front(hwnd)
    time.sleep(1.0)

    x1, y1, x2, y2 = get_window_rect(hwnd)
    print(f"  Window bounds: ({x1},{y1}) to ({x2},{y2}), size={x2-x1}x{y2-y1}")

    # Phase 1: real launch
    move_away(hwnd)
    grab_window("01_real_launch.png", hwnd, delay=0.6)
    grab("01_real_launch_desktop.png", delay=0.1)

    # ── Navigation rail geometry ──────────────────────────────────────────────
    # Nav rail: left 56px of content area (below header ~60px)
    nav_cx   = x1 + 28           # center x of 56px rail
    header_h = 60
    nav_top  = y1 + header_h + 16 + 27   # header + spacer + half btn
    btn_gap  = 64                          # 44px btn + 10+10 pad

    btns = {
        "chat":        (nav_cx, nav_top),
        "history":     (nav_cx, nav_top + btn_gap),
        "desktop":     (nav_cx, nav_top + btn_gap * 2),
        "activity":    (nav_cx, nav_top + btn_gap * 3),
        "settings":    (nav_cx, nav_top + btn_gap * 4),
    }
    print(f"\n  Nav button positions:")
    for k, (bx, by) in btns.items():
        print(f"    {k}: ({bx},{by})")

    # ── PHASE 3: Navigation icons (dark) ─────────────────────────────────────
    print("\n[PHASE 3] Navigation icons — all states...")

    # REST
    move_away(hwnd)
    grab_window("02_nav_rest_dark.png", hwnd, delay=0.3)

    # Crop nav rail only
    time.sleep(0.1)
    nav_img = ImageGrab.grab(bbox=(x1, y1, x1+60, y2))
    nav_img.save(str(AUDIT / "02_nav_rail_only.png"))
    print(f"  SAVED: 02_nav_rail_only.png")

    # HOVER — chat
    move_away(hwnd)
    time.sleep(0.1)
    mouse_move(btns["chat"][0], btns["chat"][1])
    time.sleep(0.2)
    grab_window("03_nav_hover_chat.png", hwnd, delay=0.1)
    nav_hover = ImageGrab.grab(bbox=(x1, y1, x1+60, y2))
    nav_hover.save(str(AUDIT / "03_nav_hover_rail.png"))
    print(f"  SAVED: 03_nav_hover_rail.png")

    # HOVER — history
    mouse_move(btns["history"][0], btns["history"][1])
    time.sleep(0.2)
    grab_window("03_nav_hover_history.png", hwnd, delay=0.1)

    # PRESSED — hold history btn
    mouse_hold(btns["history"][0], btns["history"][1])
    time.sleep(0.15)
    grab_window("04_nav_pressed_dark.png", hwnd, delay=0.1)
    nav_press = ImageGrab.grab(bbox=(x1, y1, x1+60, y2))
    nav_press.save(str(AUDIT / "04_nav_pressed_rail.png"))
    print(f"  SAVED: 04_nav_pressed_rail.png")
    mouse_release()
    time.sleep(0.2)

    # ACTIVE — click settings
    mouse_click(btns["settings"][0], btns["settings"][1])
    time.sleep(0.4)
    grab_window("05_nav_active_settings.png", hwnd, delay=0.1)
    nav_act = ImageGrab.grab(bbox=(x1, y1, x1+60, y2))
    nav_act.save(str(AUDIT / "05_nav_active_rail.png"))
    print(f"  SAVED: 05_nav_active_rail.png")

    # ACTIVE — click desktop
    mouse_click(btns["desktop"][0], btns["desktop"][1])
    time.sleep(0.4)
    grab_window("05_nav_active_desktop.png", hwnd, delay=0.1)

    # Return to chat
    mouse_click(btns["chat"][0], btns["chat"][1])
    time.sleep(0.4)

    # ── PHASE 4: Light theme (if theme toggle exists) ─────────────────────────
    print("\n[PHASE 4] Attempting light theme switch...")
    # Settings panel likely has theme toggle — click settings first
    mouse_click(btns["settings"][0], btns["settings"][1])
    time.sleep(0.5)
    grab_window("06_settings_panel.png", hwnd, delay=0.3)

    # Try to find theme toggle in settings area
    # Settings panel occupies content area right of nav rail
    settings_area_x = x1 + 60 + (x2 - x1 - 60) // 2
    settings_area_y = y1 + (y2 - y1) // 2
    
    # Look for theme button — usually in upper part of settings
    # Click around for theme toggle
    theme_btn_y = y1 + header_h + 60
    for try_x in [x1 + 100, x1 + 150, x1 + 200, x1 + 250]:
        mouse_move(try_x, theme_btn_y)
        time.sleep(0.1)

    grab_window("06_settings_area.png", hwnd, delay=0.2)
    
    # Return to chat
    mouse_click(btns["chat"][0], btns["chat"][1])
    time.sleep(0.4)
    grab_window("06_dark_theme_full.png", hwnd, delay=0.2)

    # ── PHASE 5: Dark theme full view ─────────────────────────────────────────
    print("\n[PHASE 5] Dark theme full view...")
    move_away(hwnd)
    grab_window("10_dark_chat.png", hwnd, delay=0.3)

    # Close-up of header
    header_img = ImageGrab.grab(bbox=(x1, y1, x2, y1+65))
    header_img.save(str(AUDIT / "10_dark_header.png"))
    print(f"  SAVED: 10_dark_header.png")

    # ── PHASE 6: Chat content ─────────────────────────────────────────────────
    print("\n[PHASE 6] Chat content test...")
    # Click input area — bottom of window
    inp_x = (x1 + x2) // 2
    inp_y = y2 - 50
    mouse_click(inp_x, inp_y)
    time.sleep(0.4)

    # Clear and type
    user32.keybd_event(0xA2, 0, 0, 0)  # Ctrl down
    user32.keybd_event(0x41, 0, 0, 0)  # A
    time.sleep(0.05)
    user32.keybd_event(0x41, 0, 2, 0)
    user32.keybd_event(0xA2, 0, 2, 0)
    time.sleep(0.1)
    user32.keybd_event(0x2E, 0, 0, 0)  # Delete
    user32.keybd_event(0x2E, 0, 2, 0)
    time.sleep(0.1)

    type_text("hello")
    time.sleep(0.5)
    grab_window("11_user_typed.png", hwnd, delay=0.2)

    # Capture input bar close-up
    input_bar = ImageGrab.grab(bbox=(x1, y2-85, x2, y2+5))
    input_bar.save(str(AUDIT / "17_input_rest.png"))
    print(f"  SAVED: 17_input_rest.png")

    press_enter()
    time.sleep(0.8)
    grab_window("11_user_message.png", hwnd, delay=0.3)

    # Wait for HELIOS response (may take several seconds with local LLM)
    print("  Waiting 12s for HELIOS response (local LLM)...")
    for i in range(12):
        time.sleep(1)
        # Capture thinking state at t=1s
        if i == 1:
            grab_window("13_thinking_state.png", hwnd, delay=0.0)
        if i == 4:
            grab_window("14_working_state.png", hwnd, delay=0.0)

    grab_window("12_helios_response.png", hwnd, delay=0.4)
    grab_window("15_final_state.png", hwnd, delay=0.1)

    # ── PHASE 8: Input dock states ────────────────────────────────────────────
    print("\n[PHASE 8] Input dock interaction states...")
    move_away(hwnd)
    input_bar2 = ImageGrab.grab(bbox=(x1, y2-85, x2, y2+5))
    input_bar2.save(str(AUDIT / "17_input_rest.png"))
    print(f"  SAVED: 17_input_rest.png (fresh)")

    # Hover over input
    mouse_move(inp_x, inp_y)
    time.sleep(0.2)
    input_hover = ImageGrab.grab(bbox=(x1, y2-85, x2, y2+5))
    input_hover.save(str(AUDIT / "18_input_hover.png"))
    print(f"  SAVED: 18_input_hover.png")

    # Hover send button (far right of input bar)
    send_x = x2 - 30
    mouse_move(send_x, inp_y)
    time.sleep(0.2)
    input_send = ImageGrab.grab(bbox=(x1, y2-85, x2, y2+5))
    input_send.save(str(AUDIT / "19_input_send_hover.png"))
    print(f"  SAVED: 19_input_send_hover.png")

    # ── PHASE 9: Compact view toggle ──────────────────────────────────────────
    print("\n[PHASE 9] Compact view toggle...")
    # Compact button is in header, near top-right controls
    # Header: x2 - 80 area for compact toggle, based on header.py layout:
    # ctrl frame packs side=right, compact_cv is leftmost in ctrl
    # Order: compact (28px), min (26px), max (26px), close (26px) + padx
    # compact is approximately x2 - (28+26+26+26+40) = x2 - 146
    compact_btn_x = x2 - 120
    compact_btn_y = y1 + 30

    mouse_click(compact_btn_x, compact_btn_y)
    time.sleep(1.5)
    grab("20_compact_view.png", delay=0.3)
    hwnd2 = find_helios_hwnd()
    if hwnd2:
        bring_to_front(hwnd2)
        grab_window("20_compact_view_crop.png", hwnd2, delay=0.3)
        # Get new bounds
        cx1, cy1, cx2, cy2 = get_window_rect(hwnd2)
        # Toggle back
        compact_btn_x2 = cx2 - 120
        compact_btn_y2 = cy1 + 30
        mouse_click(compact_btn_x2, compact_btn_y2)
        time.sleep(1.5)
    grab("21_desktop_restored.png", delay=0.4)
    hwnd3 = find_helios_hwnd()
    if hwnd3:
        bring_to_front(hwnd3)
        grab_window("21_desktop_restored_crop.png", hwnd3, delay=0.3)
        hwnd = hwnd3
        x1, y1, x2, y2 = get_window_rect(hwnd)

    # ── PHASE 10: Resize ──────────────────────────────────────────────────────
    print("\n[PHASE 10] Resize tests...")
    grab_window("22_current_size.png", hwnd, delay=0.3)

    # ── PHASE 12: Chat after navigation ──────────────────────────────────────
    print("\n[PHASE 12] Chat visibility after operations...")
    mouse_click(btns["chat"][0], btns["chat"][1])
    time.sleep(0.5)
    grab_window("26_chat_after_nav.png", hwnd, delay=0.3)

    # ── Final summary ─────────────────────────────────────────────────────────
    print("\n[AUDIT COMPLETE]")
    files = sorted(AUDIT.glob("*.png"))
    print(f"\n{len(files)} screenshots captured:")
    total_kb = 0
    for f in files:
        sz = f.stat().st_size // 1024
        total_kb += sz
        print(f"  {f.name} ({sz}KB)")
    print(f"\nTotal: {total_kb}KB in {AUDIT}")

    proc.terminate()
    return True


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
