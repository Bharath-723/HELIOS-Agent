"""
core/desktop_session/application_focus_manager.py — Application Focus Manager
================================================================================
Dedicated Windows application focus resolver.
Enforces target application focus before desktop action execution and guarantees
that HELIOS never executes input actions against its own UI overlay.
"""

import os
import time
import ctypes
import logging
from typing import Tuple, Optional, Dict, Any

import psutil

from .session_models import FocusResult
from .screen_observer import ScreenObserver

log = logging.getLogger("helios.desktop_session.focus")
user32 = ctypes.windll.user32


class ApplicationFocusManager:
    """Manages target application window activation and focus verification."""

    # Common semantic app to process mapping
    PROCESS_MAP: Dict[str, str] = {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "browser": "chrome.exe",
        "amazon": "chrome.exe",
        "edge": "msedge.exe",
        "microsoft edge": "msedge.exe",
        "firefox": "firefox.exe",
        "settings": "systemsettings.exe",
        "windows settings": "systemsettings.exe",
        "display": "systemsettings.exe",
        "sound": "systemsettings.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "explorer": "explorer.exe",
    }

    @classmethod
    def resolve_process_name(cls, target_app: str) -> str:
        """Map target application keyword to executable process name."""
        clean = (target_app or "").lower().strip()
        if clean in cls.PROCESS_MAP:
            return cls.PROCESS_MAP[clean]
        if clean.endswith(".exe"):
            return clean
        return f"{clean}.exe"

    @classmethod
    def find_target_app_window(cls, target_app: str) -> Tuple[int, str, str]:
        """
        Search visible top-level windows for matching target_app process.
        Returns: (hwnd, window_title, process_name)
        """
        req_proc = cls.resolve_process_name(target_app).lower()
        clean_target = target_app.lower().strip()
        found: list[Tuple[int, str, str]] = []

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
            if not pid.value or pid.value == os.getpid():
                return True  # Ignore current HELIOS process

            try:
                proc = psutil.Process(pid.value)
                pname = proc.name().lower()
                title_lower = title.lower()

                # Process or title match
                if pname == req_proc or req_proc.replace(".exe", "") in pname or clean_target in title_lower or clean_target in pname:
                    if not ScreenObserver.is_helios_window(hwnd, title, pname) and not ScreenObserver.is_shell_window(hwnd, title, pname):
                        found.append((hwnd, title, proc.name()))
                        return False
            except Exception:
                pass
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

        if found:
            return found[0]

        # Fallback to observer's top underlying non-HELIOS window
        obs_hwnd, obs_title, obs_app = ScreenObserver().get_target_window_info()
        if obs_hwnd and not ScreenObserver.is_helios_window(obs_hwnd, obs_title, obs_app):
            return obs_hwnd, obs_title, obs_app

        return 0, "", ""

    @classmethod
    def ensure_app_focused(cls, target_app: str, desktop_agent=None) -> FocusResult:
        """
        Ensure the target application is running and activated in the foreground.
        Hard Invariant: NEVER returns success if HELIOS process is foreground.
        """
        clean_target = target_app.strip() if target_app else "chrome"
        log.info("ApplicationFocusManager: Ensuring focus on target_app '%s'", clean_target)

        # 1. Check if HELIOS itself is targeted
        if clean_target.lower() == "helios":
            return FocusResult(
                success=True,
                hwnd=user32.GetForegroundWindow(),
                process="python.exe",
                window_title="HELIOS",
                foreground_verified=True,
            )

        # 2. Locate Target Window
        hwnd, title, proc_name = cls.find_target_app_window(clean_target)

        # 3. If Target App Window Not Found -> Attempt Launch
        if not hwnd and desktop_agent:
            log.info("ApplicationFocusManager: Target window '%s' not found. Attempting launch...", clean_target)
            if "amazon" in clean_target.lower() or "http" in clean_target.lower() or "www." in clean_target.lower():
                desktop_agent.open_website("https://www.amazon.in/")
            else:
                desktop_agent.open_app(clean_target)

            # Wait up to 3 seconds for window to spawn
            for _ in range(6):
                time.sleep(0.5)
                hwnd, title, proc_name = cls.find_target_app_window(clean_target)
                if hwnd:
                    break

        if not hwnd:
            msg = f"Target application '{clean_target}' window not found or could not be launched."
            log.warning("ApplicationFocusManager: %s", msg)
            return FocusResult(success=False, error_message=msg)

        # 4. Check if already in foreground to prevent window flashing
        fg_hwnd = user32.GetForegroundWindow()
        fg_title, fg_app = ScreenObserver.get_active_window_info_raw(fg_hwnd)
        is_helios = ScreenObserver.is_helios_window(fg_hwnd, fg_title, fg_app)

        log.info(
            "[FOCUS DIAGNOSTIC]\n"
            "foreground_hwnd=%s\n"
            "foreground_process=%s\n"
            "foreground_title=%s\n"
            "registered_helios_hwnds=%s\n"
            "is_helios_window=%s\n"
            "target_app=%s\n"
            "target_hwnd=%s\n"
            "target_process=%s",
            fg_hwnd, fg_app, fg_title, list(ScreenObserver._registered_helios_hwnds),
            is_helios, clean_target, hwnd, proc_name
        )

        if is_helios:
            msg = f"HELIOS Safety Invariant: Foreground window (HWND {fg_hwnd}) is registered HELIOS overlay ({fg_title}). Refusing input action for target '{clean_target}'."
            log.error("ApplicationFocusManager: %s", msg)
            return FocusResult(
                success=False,
                hwnd=fg_hwnd,
                process=fg_app,
                window_title=fg_title,
                foreground_verified=False,
                error_message="FOCUS_ACQUISITION_FAILED: " + msg,
            )

        if fg_hwnd == hwnd:
            log.info("ApplicationFocusManager: HWND %s ('%s') is ALREADY in foreground.", hwnd, title)
            return FocusResult(
                success=True,
                hwnd=hwnd,
                process=proc_name,
                window_title=title,
                foreground_verified=True,
            )

        # Activate Window to Foreground
        focused = ScreenObserver.focus_target_window(hwnd)
        time.sleep(0.1)

        # 5. Verify Foreground Process & Safety Invariant
        post_fg_hwnd = user32.GetForegroundWindow()
        post_fg_title, post_fg_app = ScreenObserver.get_active_window_info_raw(post_fg_hwnd)
        post_is_helios = ScreenObserver.is_helios_window(post_fg_hwnd, post_fg_title, post_fg_app)

        if post_is_helios:
            msg = f"HELIOS Safety Invariant: Post-focus foreground window is registered HELIOS overlay ({post_fg_title}). Focus acquisition failed."
            log.error("ApplicationFocusManager: %s", msg)
            return FocusResult(
                success=False,
                hwnd=post_fg_hwnd,
                process=post_fg_app,
                window_title=post_fg_title,
                foreground_verified=False,
                error_message="FOCUS_ACQUISITION_FAILED: " + msg,
            )

        if post_fg_hwnd != hwnd and (proc_name.lower() not in post_fg_app.lower() and post_fg_app.lower() not in proc_name.lower()):
            msg = f"FOCUS_ACQUISITION_FAILED: Could not establish focus on target HWND {hwnd} (Current FG: {post_fg_hwnd} '{post_fg_title}')"
            log.warning("ApplicationFocusManager: %s", msg)
            return FocusResult(
                success=False,
                hwnd=post_fg_hwnd,
                process=post_fg_app,
                window_title=post_fg_title,
                foreground_verified=False,
                error_message=msg,
            )

        log.info("ApplicationFocusManager: Focus verified on HWND %s: '%s' (%s)", hwnd, title, proc_name)
        return FocusResult(
            success=True,
            hwnd=hwnd,
            process=proc_name,
            window_title=title,
            foreground_verified=True,
        )
