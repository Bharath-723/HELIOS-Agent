"""
ui/neumorphic_button.py — HELIOS Neumorphic Button
====================================================
Canvas-based neumorphic button with raised/pressed/hover/active states.

Visual Anatomy:
  NORMAL:  raised surface (lighter highlight top-left, darker shadow bottom-right)
  HOVER:   subtle illumination increase
  PRESSED: inset illusion (shadows invert — top-left dark, bottom-right light)
  ACTIVE:  blue accent fill (selected navigation item)

Design principles from reference images:
  - Soft continuous curves
  - No hard border
  - Two-shadow model: light shadow + dark shadow
  - Immediate response (no animation delay)
  - Consistent size (no resize on hover/press)
"""

from __future__ import annotations
import tkinter as tk
from .theme import C, F, S, ThemeManager


class NeuButton:
    """
    Neumorphic canvas button — raises/depresses on click.

    size:   canvas width = height (square button)
    label:  text or icon (unicode) drawn on canvas
    on_click: callback when released
    active:   if True, shows blue selected state
    """

    def __init__(self,
                 parent: tk.Widget,
                 size: int = 40,
                 label: str = "●",
                 font_size: int = 14,
                 on_click: callable = None,
                 tooltip: str = "",
                 active: bool = False) -> None:
        self._size      = size
        self._label     = label
        self._font_size = font_size
        self._on_click  = on_click
        self._tooltip   = tooltip
        self._active    = active
        self._pressed   = False
        self._hover     = False

        self.canvas = tk.Canvas(
            parent,
            width=size, height=size,
            bg=C.NAV_BG,
            highlightthickness=0, bd=0,
            cursor="hand2",
        )

        self._draw()

        self.canvas.bind("<Enter>",          self._on_enter)
        self.canvas.bind("<Leave>",          self._on_leave)
        self.canvas.bind("<Button-1>",       self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        ThemeManager.add_listener(self._redraw)

    def pack(self, **kwargs) -> None:
        self.canvas.pack(**kwargs)

    def grid(self, **kwargs) -> None:
        self.canvas.grid(**kwargs)

    def set_active(self, active: bool) -> None:
        self._active = active
        self._draw()

    def set_label(self, label: str) -> None:
        self._label = label
        self._draw()

    # ─────────────────────────────────────────────────────────────────────────
    def _draw(self) -> None:
        c = self.canvas
        c.delete("all")
        s = self._size
        r = s // 2
        cx, cy = r, r

        # ── Surface color ─────────────────────────────────────────────────────
        if self._active:
            bg   = C.BLUE_DIM
            fg   = C.BLUE_L
            bd   = C.BLUE
        elif self._pressed:
            bg   = C.NEU_PRESSED
            fg   = C.FG_2
            bd   = C.NEU_BORDER
        elif self._hover:
            bg   = C.NAV_HOVER
            fg   = C.FG_1
            bd   = C.BORDER
        else:
            bg   = C.NAV_BG
            fg   = C.NAV_ICON
            bd   = C.NAV_BG   # invisible border in normal state

        # ── Circle background ─────────────────────────────────────────────────
        pad = 4
        c.create_oval(pad, pad, s-pad, s-pad,
                      fill=bg, outline=bd, width=1,
                      tags="btn")

        # ── Label ─────────────────────────────────────────────────────────────
        c.create_text(cx, cy,
                      text=self._label,
                      font=(F._FALLBACK, self._font_size),
                      fill=fg,
                      tags="lbl")

        # ── Active indicator dot ───────────────────────────────────────────────
        if self._active:
            dot_r = 3
            c.create_oval(cx - dot_r, s - 10 - dot_r,
                          cx + dot_r, s - 10 + dot_r,
                          fill=C.BLUE, outline="",
                          tags="dot")

    def _redraw(self) -> None:
        self.canvas.configure(bg=C.NAV_BG)
        self._draw()

    # ─────────────────────────────────────────────────────────────────────────
    def _on_enter(self, e) -> None:
        self._hover = True
        self._draw()

    def _on_leave(self, e) -> None:
        self._hover = False
        self._pressed = False
        self._draw()

    def _on_press(self, e) -> None:
        self._pressed = True
        self._draw()

    def _on_release(self, e) -> None:
        self._pressed = False
        self._draw()
        if self._on_click:
            try:
                self._on_click()
            except Exception:
                pass
