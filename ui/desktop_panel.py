"""
ui/desktop_panel.py — HELIOS Real Desktop Agent Dashboard
==========================================================
Live desktop automation status dashboard:
  - AGENT STATUS: Ready / Running / Waiting / Error
  - ACTIVE APPLICATION: Real Win32 foreground window name
  - CURRENT TASK: Description of desktop automation command
  - CURRENT ACTION: Action step (Opening browser, Navigating, Clicking, Verifying)
  - BROWSER & IPC: Browser domain and agent IPC connection state
  - MODEL: Current active LLM
"""

from __future__ import annotations
import sys
import datetime
import tkinter as tk
from .theme import C, F, ThemeManager
from .stat_card import StatCard


def _get_active_window_title() -> str:
    if sys.platform != "win32":
        return "Desktop Environment"
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return "Desktop"
        buf = ctypes.create_unicode_buffer(512)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 512)
        title = buf.value.strip()
        return title if title else "Desktop"
    except Exception:
        return "Desktop"


class DesktopPanel:
    """
    Real Desktop Agent status dashboard.
    Never shows a blank page.
    """

    def __init__(self, parent: tk.Widget) -> None:
        self.frame = tk.Frame(parent, bg=C.BG_S)
        self._is_active_task = False

        # Scrollable container
        self._canvas = tk.Canvas(self.frame, bg=C.BG_S, highlightthickness=0)
        self._vsb    = tk.Scrollbar(self.frame, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)

        self._canvas.pack(side="left", fill="both", expand=True)
        self._vsb.pack(side="right", fill="y")

        self._inner = tk.Frame(self._canvas, bg=C.BG_S)
        self._win   = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._win, width=e.width))
        self._canvas.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"))

        self._build()
        self._bind_scroll(self._inner)
        ThemeManager.add_listener(self._on_theme_changed)

    def _bind_scroll(self, w: tk.Widget) -> None:
        try:
            w.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
            for child in w.winfo_children():
                self._bind_scroll(child)
        except Exception:
            pass

    def _build(self) -> None:
        pad = 12

        # ── Header ─────────────────────────────────────────────────────────────
        hdr = tk.Frame(self._inner, bg=C.BG_S)
        hdr.pack(fill="x", padx=pad, pady=(16, 12))

        tk.Label(hdr, text="DESKTOP AGENT",
                 font=(F._PRIMARY, F.LG, "bold"),
                 bg=C.BG_S, fg=C.FG_1).pack(side="left")

        self._status_chip = tk.Label(hdr, text="● Ready",
                                     font=(F._FALLBACK, F.XS, "bold"),
                                     bg=C.OK_D if hasattr(C, 'OK_D') else "#111B3A",
                                     fg=C.OK, padx=8, pady=3)
        self._status_chip.pack(side="right")

        # ── Row 1: Agent & Active App ─────────────────────────────────────────
        row1 = tk.Frame(self._inner, bg=C.BG_S)
        row1.pack(fill="x", padx=pad, pady=(0, 14))

        self._agent_card = StatCard(row1, title="AGENT STATUS",
                                    primary="● READY", primary_label="Controller",
                                    secondary="Idle", secondary_label="State",
                                    accent_color=C.OK)
        self._agent_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        curr_app = _get_active_window_title()
        self._app_card = StatCard(row1, title="ACTIVE APP",
                                  primary=curr_app[:20], primary_label="Foreground",
                                  secondary="Local OS", secondary_label="Environment",
                                  accent_color=C.BLUE)
        self._app_card.pack(side="left", fill="both", expand=True)

        # ── Row 2: Task & Action ───────────────────────────────────────────────
        row2 = tk.Frame(self._inner, bg=C.BG_S)
        row2.pack(fill="x", padx=pad, pady=(0, 14))

        self._task_card = StatCard(row2, title="CURRENT TASK",
                                   primary="No Active Task", primary_label="Task Details",
                                   accent_color=C.CYAN)
        self._task_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._action_card = StatCard(row2, title="CURRENT ACTION",
                                     primary="Waiting", primary_label="Status",
                                     accent_color=C.WARN)
        self._action_card.pack(side="left", fill="both", expand=True)

        # ── Row 3: Browser & Model ─────────────────────────────────────────────
        row3 = tk.Frame(self._inner, bg=C.BG_S)
        row3.pack(fill="x", padx=pad, pady=(0, 16))

        self._browser_card = StatCard(row3, title="BROWSER",
                                      primary="Ready", primary_label="Browser Service",
                                      accent_color=C.BLUE)
        self._browser_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._model_card = StatCard(row3, title="ACTIVE MODEL",
                                    primary="gemma3", primary_label="On-Device AI",
                                    secondary="● LOCAL", accent_color=C.OK)
        self._model_card.pack(side="left", fill="both", expand=True)

        # ── Empty State Container ──────────────────────────────────────────────
        self._empty_container = tk.Frame(self._inner, bg=C.GLASS_3, padx=20, pady=24,
                                          highlightthickness=1, highlightbackground=C.GLASS_BD_3)
        self._empty_container.pack(fill="x", padx=pad, pady=(0, 16))

        tk.Label(self._empty_container, text="DESKTOP AGENT READY",
                 font=(F._PRIMARY, F.SM, "bold"), bg=C.GLASS_3, fg=C.FG_1).pack(anchor="w")

        tk.Label(self._empty_container,
                 text="No active desktop automation task.\nStart a command from the HELIOS input dock below (e.g. 'open browser', 'search web', 'take screenshot').",
                 font=(F._FALLBACK, F.SM), bg=C.GLASS_3, fg=C.FG_3, justify="left", pady=6).pack(anchor="w")

    def update_desktop_state(self, state: str = "Ready", task: str = "", action: str = "", app: str = "", model: str = "gemma3") -> None:
        try:
            curr_app = app or _get_active_window_title()
            self._app_card.update(primary=curr_app[:24])
            self._model_card.update(primary=model)

            if task:
                self._is_active_task = True
                self._empty_container.pack_forget()
                self._agent_card.update(primary=f"● {state.upper()}", secondary="Active")
                self._task_card.update(primary=task[:30])
                self._action_card.update(primary=action[:30] if action else "Executing...")
                self._status_chip.configure(text=f"● {state}", fg=C.STATE_WORKING)
            else:
                self._is_active_task = False
                self._empty_container.pack(fill="x", padx=16, pady=(0, 16))
                self._agent_card.update(primary="● READY", secondary="Idle")
                self._task_card.update(primary="No Active Task")
                self._action_card.update(primary="Waiting")
                self._status_chip.configure(text="● Ready", fg=C.OK)
        except Exception:
            pass

    def refresh(self) -> None:
        try:
            curr_app = _get_active_window_title()
            self._app_card.update(primary=curr_app[:24])
            self._canvas.update_idletasks()
            w = self._canvas.winfo_width()
            if w > 10:
                self._canvas.itemconfig(self._win, width=w)
                self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        except Exception:
            pass

    def _on_theme_changed(self) -> None:
        try:
            self.frame.configure(bg=C.BG_S)
            self._canvas.configure(bg=C.BG_S)
            self._inner.configure(bg=C.BG_S)
        except Exception:
            pass
