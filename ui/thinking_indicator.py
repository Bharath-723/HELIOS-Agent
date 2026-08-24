"""
ui/thinking_indicator.py — HELIOS v4.0 9-State Indicator
==========================================================
Minimal inline cognitive-state indicator.

Design:
  • Floats inline in chat (transparent to chat surface)
  • Static colored dot + state label + optional sub-label
  • State updates are immediate text mutations — no animation loop
  • Disappears immediately when response arrives

States:
  IDLE       → grey dot   + "Ready"
  THINKING   → blue dot   + "Thinking · · ·"
  ANALYZING  → blue dot   + "Analyzing · · ·"
  WORKING    → cyan dot   + "Working · · ·"
  VERIFYING  → amber dot  + "Verifying · · ·"
  WAITING    → cyan dot   + "Waiting for input"
  SUCCESS    → green dot  + "Done"
  WARNING    → amber dot  + "Warning"
  ERROR      → red dot    + "Error"
  STOPPED    → grey dot   + "Stopped"
"""

from __future__ import annotations
import tkinter as tk
from .theme import C, F, S, ThemeManager


# State → (dot_color, label_text, sub_label)
_STATES: dict[str, tuple[str, str, str]] = {
    "idle":       ("FG_3",    "Ready",               ""),
    "thinking":   ("BLUE",    "Thinking · · ·",      ""),
    "analyzing":  ("BLUE",    "Analyzing · · ·",     ""),
    "generating": ("BLUE_L",  "Generating · · ·",    ""),
    "searching":  ("CYAN",    "Searching · · ·",     ""),
    "working":    ("CYAN",    "Working · · ·",       ""),
    "verifying":  ("WARN",    "Verifying · · ·",     ""),
    "waiting":    ("CYAN",    "Waiting for input",   ""),
    "success":    ("OK",      "Done",                ""),
    "warning":    ("WARN",    "Warning",             ""),
    "error":      ("ERR",     "Error",               ""),
    "stopped":    ("FG_3",    "Stopped",             ""),
}


class ThinkingIndicator:
    """
    Minimal inline state indicator — colored dot + text label.
    All state transitions are immediate widget.configure() calls.
    No animation loop, no blocking, no opacity changes.
    """

    def __init__(self, parent: tk.Widget, anim_engine=None) -> None:
        self._engine = anim_engine
        self._state  = "thinking"

        # Transparent frame — blends with chat background
        self.frame = tk.Frame(parent, bg=C.BG_S)
        self.frame.pack(fill="x", padx=14, pady=(6, 2))

        self._build()
        ThemeManager.add_listener(self._on_theme_changed)

    # ─────────────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        self.inner = tk.Frame(self.frame, bg=C.BG_S, padx=4, pady=6)
        self.inner.pack(anchor="w")

        # State dot — colored circle emoji approach
        dot_color_key, label_text, _ = _STATES.get(self._state, _STATES["thinking"])
        dot_color = getattr(C, dot_color_key, C.BLUE)

        self.dot_lbl = tk.Label(
            self.inner,
            text="●",
            font=(F._FALLBACK, F.XS),
            bg=C.BG_S, fg=dot_color,
        )
        self.dot_lbl.pack(side="left", padx=(0, 6))

        # State label
        self.state_lbl = tk.Label(
            self.inner,
            text=label_text,
            font=(F._PRIMARY, F.SM),
            bg=C.BG_S, fg=C.FG_3,
        )
        self.state_lbl.pack(side="left")

        # Notify animation engine (sets thinking orbs active, if applicable)
        if self._engine:
            try:
                self._engine.set_thinking(True, None, [])
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────────────
    def set_state(self, state: str, sub_label: str = "") -> None:
        """
        Transition to a named state immediately.
        All updates are simple widget.configure() — no delay, no loop.
        """
        self._state = state.lower()
        dot_color_key, label_text, _ = _STATES.get(self._state, _STATES["thinking"])
        dot_color = getattr(C, dot_color_key, C.BLUE)
        try:
            self.dot_lbl.configure(fg=dot_color)
            self.state_lbl.configure(text=label_text if not sub_label else sub_label)
        except Exception:
            pass

    def set_label(self, state: str) -> None:
        """Backward-compatible alias for set_state()."""
        self.set_state(state)

    # ─────────────────────────────────────────────────────────────────────────
    def destroy(self) -> None:
        if self._engine:
            try:
                self._engine.set_thinking(False)
            except Exception:
                pass
        try:
            self.frame.destroy()
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    def _on_theme_changed(self) -> None:
        try:
            dot_color_key, _, _ = _STATES.get(self._state, _STATES["thinking"])
            dot_color = getattr(C, dot_color_key, C.BLUE)
            self.frame.configure(bg=C.BG_S)
            self.inner.configure(bg=C.BG_S)
            self.dot_lbl.configure(bg=C.BG_S, fg=dot_color)
            self.state_lbl.configure(bg=C.BG_S, fg=C.FG_3)
        except Exception:
            pass
