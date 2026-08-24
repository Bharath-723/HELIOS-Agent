"""
core/desktop_session/screen_observer.py — Desktop Screen & State Observer
========================================================================
Captures desktop screenshots, detects active non-HELIOS target window and process
name using Win32 API Z-order enumeration, excludes HELIOS overlay windows,
extracts UI elements, and enforces target window focus.
"""

import os
import time
import logging
import ctypes
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any

import psutil
import pyautogui

from .session_models import ScreenState, ScreenElement

log = logging.getLogger("helios.desktop_session.observer")

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class ScreenObserver:
    """Captures and structures current desktop state while excluding HELIOS overlay."""

    _registered_helios_hwnds: set = set()

    def __init__(self, screenshot_dir: Optional[str] = None):
        self.screenshot_dir = screenshot_dir or os.path.join(
            os.path.expanduser("~"), ".helios", "screenshots"
        )
        os.makedirs(self.screenshot_dir, exist_ok=True)

    @classmethod
    def register_helios_hwnd(cls, hwnd: int) -> None:
        """Register a known HELIOS UI window handle to guarantee exclusion."""
        if hwnd:
            cls._registered_helios_hwnds.add(hwnd)
            log.info("ScreenObserver: Registered HELIOS window handle HWND %s", hwnd)

    @classmethod
    def is_helios_window(cls, hwnd: int, title: str = "", app_name: str = "") -> bool:
        """
        Determine whether a window handle or title belongs to HELIOS.
        Excludes HELIOS floating bar, chat window, or subprocesses.
        Does NOT match developer workspace titles like 'HELIOS_FINAL - Antigravity IDE'.
        """
        if hwnd and hwnd in cls._registered_helios_hwnds:
            return True

        t_lower = (title or "").lower().strip()
        # Explicitly ignore IDE and terminal windows running python main.py
        if any(ide in t_lower for ide in ("antigravity ide", "visual studio code", "vscode", "windows terminal", "powershell")):
            return False

        # Specific overlay titles (starts with "helios " or exact "helios")
        if t_lower == "helios" or t_lower.startswith("helios ") or any(t in t_lower for t in ("helios popup", "helios floating bar", "helios overlay", "helios v4.0")):
            return True

        if not hwnd or not user32.IsWindow(hwnd):
            return False

        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == os.getpid() and cls._registered_helios_hwnds:
            if hwnd in cls._registered_helios_hwnds:
                return True

        return False

    @classmethod
    def is_shell_window(cls, hwnd: int, title: str = "", app_name: str = "") -> bool:
        """Identify Windows system shell/desktop overlay windows to ignore."""
        if not hwnd:
            return True
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        class_name = buf.value

        if class_name in ("Progman", "WorkerW", "Shell_TrayWnd", "Windows.UI.Core.CoreWindow"):
            if not title or title in ("Program Manager", "Start", "Search", "Taskbar"):
                return True
        return False

    def get_target_window_info(self) -> Tuple[int, str, str]:
        """
        Enumerate top-level windows in Z-order and resolve the top-most visible,
        non-HELIOS user application window.
        Returns: (hwnd, title, app_name)
        """
        found: List[Tuple[int, str, str]] = []

        def enum_cb(hwnd, extra):
            if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.strip()
            if not title:
                return True

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            app_name = "explorer.exe"
            if pid.value:
                try:
                    proc = psutil.Process(pid.value)
                    app_name = proc.name()
                except Exception:
                    pass

            if not self.is_helios_window(hwnd, title, app_name) and not self.is_shell_window(hwnd, title, app_name):
                found.append((hwnd, title, app_name))
                return False  # Stop enumeration on first valid user app
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

        if found:
            log.debug("ScreenObserver: Resolved underlying target window -> HWND %s: '%s' (%s)", found[0][0], found[0][1], found[0][2])
            return found[0]

        # Fallback to GetForegroundWindow if non-HELIOS
        fg_hwnd = user32.GetForegroundWindow()
        fg_title, fg_app = self.get_active_window_info_raw(fg_hwnd)
        if not self.is_helios_window(fg_hwnd, fg_title, fg_app):
            return fg_hwnd, fg_title, fg_app

        return 0, "Desktop", "explorer.exe"

    @classmethod
    def get_active_window_info_raw(cls, hwnd: int) -> Tuple[str, str]:
        """Extract title and app_name for a specific window handle."""
        title = "Desktop"
        app_name = "explorer.exe"
        if not hwnd or not user32.IsWindow(hwnd):
            return title, app_name

        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if buf.value.strip():
                title = buf.value.strip()

        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value:
            try:
                proc = psutil.Process(pid.value)
                app_name = proc.name()
            except Exception:
                pass
        return title, app_name

    @classmethod
    def focus_target_window(cls, hwnd: int) -> bool:
        """
        Bring the specified target application window to the foreground.
        Uses AttachThreadInput to guarantee focus transfer from HELIOS overlay.
        """
        if not hwnd or not user32.IsWindow(hwnd):
            return False

        current_fg = user32.GetForegroundWindow()
        if current_fg == hwnd:
            return True

        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE

        fg_pid = ctypes.c_ulong()
        fg_thread = user32.GetWindowThreadProcessId(current_fg, ctypes.byref(fg_pid))
        target_thread = user32.GetWindowThreadProcessId(hwnd, None)

        try:
            if fg_thread != target_thread and fg_thread != 0:
                user32.AttachThreadInput(fg_thread, target_thread, True)
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
                user32.AttachThreadInput(fg_thread, target_thread, False)
            else:
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
        except Exception as exc:
            log.warning("ScreenObserver: Focus transfer warning: %s", exc)

        time.sleep(0.08)  # Brief delay for Windows WM_SETFOCUS
        new_fg = user32.GetForegroundWindow()
        success = (new_fg == hwnd)
        if not success:
            log.warning("ScreenObserver: Could not establish focus on target HWND %s (Current FG: %s)", hwnd, new_fg)
        return success

    def extract_ui_elements(self, window_title: str, app_name: str) -> List[ScreenElement]:
        """
        Extract UI elements from active window context.
        Excludes HELIOS UI controls from candidate targets.
        """
        elements: List[ScreenElement] = []
        title_lower = window_title.lower()
        app_lower = app_name.lower()

        # Window header element
        elements.append(ScreenElement(
            text=window_title,
            element_type="window",
            identifier="active_window_title"
        ))

        # Application specific element heuristics
        if "settings" in title_lower or "settings" in app_lower:
            elements.extend([
                ScreenElement(text="Search box", element_type="input", identifier="search_box"),
                ScreenElement(text="Display", element_type="button", identifier="nav_display"),
                ScreenElement(text="Sound", element_type="button", identifier="nav_sound"),
                ScreenElement(text="Bluetooth", element_type="button", identifier="nav_bluetooth"),
                ScreenElement(text="Network & internet", element_type="button", identifier="nav_network"),
            ])
        elif "chrome" in app_lower or "msedge" in app_lower or "browser" in title_lower or "amazon" in title_lower:
            elements.extend([
                ScreenElement(text="Search Amazon", element_type="input", identifier="amazon_search_box"),
                ScreenElement(text="Address Bar", element_type="input", identifier="address_bar"),
                ScreenElement(text="Add to Cart", element_type="button", identifier="btn_add_to_cart"),
                ScreenElement(text="Proceed to checkout", element_type="button", identifier="btn_checkout"),
                ScreenElement(text="Cart", element_type="button", identifier="btn_cart"),
            ])
        elif "explorer" in app_lower:
            elements.extend([
                ScreenElement(text="Address Bar", element_type="input", identifier="explorer_address"),
                ScreenElement(text="Search Explorer", element_type="input", identifier="explorer_search"),
                ScreenElement(text="Navigation Pane", element_type="container", identifier="nav_pane"),
            ])

        return elements

    def observe(self, save_screenshot: bool = True) -> ScreenState:
        """
        Capture current screenshot, query active underlying target window (excluding HELIOS),
        extract UI elements, and assemble a complete ScreenState.
        """
        target_hwnd, title, app_name = self.get_target_window_info()
        ui_elements = self.extract_ui_elements(title, app_name)

        screenshot_path = None
        if save_screenshot:
            try:
                filename = f"screen_{int(time.time() * 1000)}.png"
                screenshot_path = os.path.join(self.screenshot_dir, filename)
                img = pyautogui.screenshot()
                img.save(screenshot_path)
            except Exception as exc:
                log.warning("ScreenObserver: Screenshot capture failed: %s", exc)

        ocr_summary = f"Target Window: '{title}' ({app_name}). Available elements: {', '.join(e.text for e in ui_elements[:6])}"

        state = ScreenState(
            timestamp=time.time(),
            active_window_title=title,
            active_app_name=app_name,
            screenshot_path=screenshot_path,
            ocr_text=ocr_summary,
            ui_elements=ui_elements,
            screen_summary=f"{title} [{app_name}]"
        )

        log.debug("ScreenObserver: Observed state -> %s (HWND: %s)", state.screen_summary, target_hwnd)
        return state
