"""
ui/status_chip.py — HELIOS Floating Status Capsule
====================================================
Compact glass status chip for showing system/agent state inline.

Usage:
    chip = StatusChip(parent, state="thinking", label="Thinking")
    chip.pack(padx=8, pady=4)
    chip.set_state("working", "Opening Chrome")
"""

from __future__ import annotations
import tkinter as tk
from .theme import C, F, S, ThemeManager


_STATE_COLORS = {
    "idle":       ("STATE_IDLE",      "●"),
    "thinking":   ("STATE_THINKING",  "◉"),
    "analyzing":  ("STATE_THINKING",  "◉"),
    "generating": ("STATE_THINKING",  "◉"),
    "searching":  ("STATE_WORKING",   "◉"),
    "working":    ("STATE_WORKING",   "◉"),
    "verifying":  ("STATE_VERIFYING", "◎"),
    "waiting":    ("STATE_WAITING",   "●"),
    "success":    ("STATE_SUCCESS",   "✓"),
    "warning":    ("STATE_WARNING",   "⚠"),
    "error":      ("STATE_ERROR",     "✕"),
    "stopped":    ("STATE_STOPPED",   "■"),
}


class StatusChip:
    """
    Minimal floating glass capsule showing a state dot + label.
    Instant update — no animation delay.
    """

    def __init__(self, parent: tk.Widget, state: str = "idle",
                 label: str = "Ready") -> None:
        self._state = state.lower()

        self.frame = tk.Frame(
            parent,
            bg=C.DEPTH_2,
            highlightthickness=1,
            highlightbackground=C.DEPTH_BD_2,
        )

        color_key, icon = _STATE_COLORS.get(self._state, ("STATE_IDLE", "●"))
        dot_color = getattr(C, color_key)

        self._dot = tk.Label(
            self.frame,
            text=icon,
            font=(F._FALLBACK, F.XS),
            bg=C.DEPTH_2, fg=dot_color,
        )
        self._dot.pack(side="left", padx=(8, 4), pady=4)

        self._lbl = tk.Label(
            self.frame,
            text=label,
            font=(F._FALLBACK, F.XS),
            bg=C.DEPTH_2, fg=C.FG_2,
        )
        self._lbl.pack(side="left", padx=(0, 10), pady=4)

        ThemeManager.add_listener(self._on_theme_changed)

    def pack(self, **kwargs) -> None:
        self.frame.pack(**kwargs)

    def grid(self, **kwargs) -> None:
        self.frame.grid(**kwargs)

    def set_state(self, state: str, label: str = "") -> None:
        self._state = state.lower()
        color_key, icon = _STATE_COLORS.get(self._state, ("STATE_IDLE", "●"))
        dot_color = getattr(C, color_key)
        try:
            self._dot.configure(text=icon, fg=dot_color)
            if label:
                self._lbl.configure(text=label)
        except Exception:
            pass

    def set_label(self, label: str) -> None:
        try:
            self._lbl.configure(text=label)
        except Exception:
            pass

    def _on_theme_changed(self) -> None:
        color_key, icon = _STATE_COLORS.get(self._state, ("STATE_IDLE", "●"))
        dot_color = getattr(C, color_key)
        try:
            self.frame.configure(bg=C.DEPTH_2, highlightbackground=C.DEPTH_BD_2)
            self._dot.configure(bg=C.DEPTH_2, fg=dot_color)
            self._lbl.configure(bg=C.DEPTH_2, fg=C.FG_2)
        except Exception:
            pass
