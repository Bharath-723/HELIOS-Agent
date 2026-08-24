"""
ui/action_card.py — HELIOS Desktop Action Visualization Card
=============================================================
Live-updating card showing current desktop agent action + state.

Design:
  Glass card (DEPTH_2) with left accent strip.
  State transitions update in-place — no destroy/recreate.
  Reuse the same card for multiple sequential action updates.

Usage:
    card = ActionCard(parent)
    card.pack(fill="x", padx=14, pady=4)
    card.set_action("working", "Opening Chrome", "chrome.exe")
    # later...
    card.set_action("verifying", "Checking screen state", "Amazon.com")
    # later...
    card.set_action("success", "Search completed", "Screen verified")
"""

from __future__ import annotations
import tkinter as tk
from datetime import datetime
from .theme import C, F, S, ThemeManager
from .status_chip import _STATE_COLORS


_ACCENT_MAP = {
    "idle":       "STATE_IDLE",
    "thinking":   "STATE_THINKING",
    "working":    "STATE_WORKING",
    "verifying":  "STATE_VERIFYING",
    "waiting":    "STATE_WAITING",
    "success":    "STATE_SUCCESS",
    "warning":    "STATE_WARNING",
    "error":      "STATE_ERROR",
    "stopped":    "STATE_STOPPED",
}

_TITLE_MAP = {
    "idle":       "IDLE",
    "thinking":   "THINKING",
    "working":    "WORKING",
    "verifying":  "VERIFYING",
    "waiting":    "WAITING",
    "success":    "VERIFIED",
    "warning":    "WARNING",
    "error":      "FAILED",
    "stopped":    "STOPPED",
}


class ActionCard:
    """
    Live desktop action card — updates in-place without widget recreation.
    """

    def __init__(self, parent: tk.Widget) -> None:
        self._state = "working"

        # Outer shadow frame
        self._shadow = tk.Frame(parent, bg=C.SHADOW_SM)
        self.frame   = self._shadow  # external reference

        # Card surface
        self._card = tk.Frame(
            self._shadow,
            bg=C.DEPTH_2,
            highlightthickness=1,
            highlightbackground=C.DEPTH_BD_2,
        )
        self._card.pack(fill="both", expand=True, padx=(0,1), pady=(0,1))

        # Top highlight line
        self._hl = tk.Frame(self._card, bg=C.DEPTH_BD_3, height=1)
        self._hl.pack(fill="x")

        # Row: accent strip + body
        self._row = tk.Frame(self._card, bg=C.DEPTH_2)
        self._row.pack(fill="both", expand=True)

        accent_color = getattr(C, _ACCENT_MAP.get(self._state, "STATE_WORKING"))
        self._accent = tk.Frame(self._row, bg=accent_color, width=3)
        self._accent.pack(side="left", fill="y")

        body = tk.Frame(self._row, bg=C.DEPTH_2, padx=12, pady=8)
        body.pack(fill="both", expand=True)

        # Header row
        hdr = tk.Frame(body, bg=C.DEPTH_2)
        hdr.pack(fill="x", pady=(0, 6))

        color_key, icon = _STATE_COLORS.get(self._state, ("STATE_WORKING", "◉"))
        dot_color = getattr(C, color_key)

        self._state_icon = tk.Label(hdr, text=icon, font=(F._FALLBACK, F.SM),
                                    bg=C.DEPTH_2, fg=dot_color)
        self._state_icon.pack(side="left", padx=(0, 6))

        self._state_lbl = tk.Label(hdr, text="WORKING",
                                   font=(F._PRIMARY, F.SM, "bold"),
                                   bg=C.DEPTH_2, fg=C.FG_1)
        self._state_lbl.pack(side="left")

        ts = datetime.now().strftime("%I:%M %p")
        self._ts_lbl = tk.Label(hdr, text=ts, font=(F._FALLBACK, F.XS),
                                bg=C.DEPTH_2, fg=C.FG_3)
        self._ts_lbl.pack(side="right")

        # Action line
        self._action_lbl = tk.Label(body, text="",
                                    font=(F._FALLBACK, F.MD),
                                    bg=C.DEPTH_2, fg=C.FG_1,
                                    anchor="w")
        self._action_lbl.pack(fill="x")

        # Sub-detail line
        self._detail_lbl = tk.Label(body, text="",
                                    font=(F._FALLBACK, F.XS),
                                    bg=C.DEPTH_2, fg=C.FG_3,
                                    anchor="w")
        self._detail_lbl.pack(fill="x")

        ThemeManager.add_listener(self._on_theme_changed)

    def pack(self, **kwargs) -> None:
        self._shadow.pack(**kwargs)

    def set_action(self, state: str, action: str, detail: str = "") -> None:
        """Update the card in-place — no widget recreation."""
        self._state = state.lower()
        accent_key  = _ACCENT_MAP.get(self._state, "STATE_WORKING")
        color_key, icon = _STATE_COLORS.get(self._state, ("STATE_WORKING", "◉"))
        accent_color = getattr(C, accent_key)
        dot_color    = getattr(C, color_key)
        title        = _TITLE_MAP.get(self._state, self._state.upper())
        ts           = datetime.now().strftime("%I:%M %p")
        try:
            self._accent.configure(bg=accent_color)
            self._state_icon.configure(text=icon, fg=dot_color)
            self._state_lbl.configure(text=title)
            self._action_lbl.configure(text=action)
            self._detail_lbl.configure(text=detail)
            self._ts_lbl.configure(text=ts)
        except Exception:
            pass

    def _on_theme_changed(self) -> None:
        accent_key = _ACCENT_MAP.get(self._state, "STATE_WORKING")
        color_key, _ = _STATE_COLORS.get(self._state, ("STATE_WORKING", "◉"))
        try:
            self._shadow.configure(bg=C.SHADOW_SM)
            self._card.configure(bg=C.DEPTH_2, highlightbackground=C.DEPTH_BD_2)
            self._hl.configure(bg=C.DEPTH_BD_3)
            self._row.configure(bg=C.DEPTH_2)
            self._accent.configure(bg=getattr(C, accent_key))
        except Exception:
            pass
