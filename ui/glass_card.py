"""
ui/glass_card.py — HELIOS Reusable Glass Card Surface
======================================================
A premium translucent card widget using the 5-level glass depth system.

Glass Card Anatomy (3 visual layers):
  1. Shadow frame   — offset behind card (simulated elevation)
  2. Card frame     — glass surface with border
  3. Content frame  — inner padding region

Usage:
    card = GlassCard(parent, depth=3, accent_color=C.BLUE, padding=12)
    card.pack(fill="x", pady=4)
    # Add children to card.body
    tk.Label(card.body, text="Hello", bg=card.bg).pack()
"""

from __future__ import annotations
import tkinter as tk
from .theme import C, F, S, ThemeManager


# Maps depth level → (surface_bg, border_color, highlight_color, shadow_color)
_DEPTH_MAP = {
    1: ("DEPTH_1", "DEPTH_BD_1", "GLASS_BD_2", "SHADOW_SM"),
    2: ("DEPTH_2", "DEPTH_BD_2", "GLASS_BD_3", "SHADOW_SM"),
    3: ("DEPTH_3", "DEPTH_BD_3", "GLASS_BD_4", "SHADOW_MD"),
    4: ("DEPTH_4", "DEPTH_BD_4", "GLASS_BD_5", "SHADOW_MD"),
    5: ("GLASS_5", "GLASS_BD_5", "GLASS_BD_5", "SHADOW_LG"),
}


class GlassCard:
    """
    Premium glass card with 3-layer depth simulation.

    Layer 1: shadow_frame  — dark frame 1px offset (elevation illusion)
    Layer 2: card_frame    — glass surface + border + optional top highlight
    Layer 3: body          — content padding area

    depth: 1-5 (1=lowest/darkest, 5=highest/lightest)
    accent_color: optional left vertical accent strip color (e.g. C.BLUE)
    padding: inner content padding in pixels
    corner: corner radius drawn on canvas (decorative, not tk clip)
    """

    def __init__(self,
                 parent: tk.Widget,
                 depth: int = 2,
                 accent_color: str | None = None,
                 padding: int = 12,
                 corner: int = 8,
                 show_highlight: bool = True) -> None:
        self._depth        = max(1, min(5, depth))
        self._accent_color = accent_color
        self._padding      = padding
        self._corner       = corner

        surf_key, bd_key, hl_key, sh_key = _DEPTH_MAP[self._depth]
        self.bg      = getattr(C, surf_key)
        self._bd     = getattr(C, bd_key)
        self._hl     = getattr(C, hl_key) if show_highlight else None
        self._shadow = getattr(C, sh_key)

        # ── Shadow layer (elevation illusion) ────────────────────────────────
        self.shadow_frame = tk.Frame(parent, bg=self._shadow, bd=0)

        # ── Card surface ──────────────────────────────────────────────────────
        self.frame = tk.Frame(
            self.shadow_frame,
            bg=self.bg,
            highlightthickness=1,
            highlightbackground=self._bd,
        )
        self.frame.pack(fill="both", expand=True, padx=(0, 1), pady=(0, 1))

        # ── Optional top highlight line ───────────────────────────────────────
        if show_highlight and self._hl:
            self._hl_line = tk.Frame(self.frame, bg=self._hl, height=1)
            self._hl_line.pack(fill="x")
        else:
            self._hl_line = None

        # ── Inner row: optional accent strip + body ───────────────────────────
        self._row = tk.Frame(self.frame, bg=self.bg)
        self._row.pack(fill="both", expand=True)

        if accent_color:
            self._accent = tk.Frame(self._row, bg=accent_color, width=3)
            self._accent.pack(side="left", fill="y")

        self.body = tk.Frame(self._row, bg=self.bg, padx=padding, pady=padding)
        self.body.pack(fill="both", expand=True)

        ThemeManager.add_listener(self._on_theme_changed)

    # Pack / place / grid convenience delegated to shadow_frame
    def pack(self, **kwargs) -> None:
        self.shadow_frame.pack(**kwargs)

    def grid(self, **kwargs) -> None:
        self.shadow_frame.grid(**kwargs)

    def place(self, **kwargs) -> None:
        self.shadow_frame.place(**kwargs)

    def pack_forget(self) -> None:
        self.shadow_frame.pack_forget()

    def destroy(self) -> None:
        try:
            self.shadow_frame.destroy()
        except Exception:
            pass

    def configure_accent(self, color: str) -> None:
        if hasattr(self, "_accent"):
            self._accent.configure(bg=color)

    def _on_theme_changed(self) -> None:
        surf_key, bd_key, hl_key, sh_key = _DEPTH_MAP[self._depth]
        self.bg      = getattr(C, surf_key)
        self._bd     = getattr(C, bd_key)
        self._hl     = getattr(C, hl_key)
        self._shadow = getattr(C, sh_key)
        try:
            self.shadow_frame.configure(bg=self._shadow)
            self.frame.configure(bg=self.bg, highlightbackground=self._bd)
            if self._hl_line:
                self._hl_line.configure(bg=self._hl)
            self._row.configure(bg=self.bg)
            self.body.configure(bg=self.bg)
        except Exception:
            pass
