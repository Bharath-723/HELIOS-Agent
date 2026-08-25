"""
ui/stat_card.py — HELIOS Statistics Card (Reference 3)
=======================================================
Compact glass statistic card inspired by the reference fitness UI:
  - Soft glass surface
  - Large primary metric
  - Small label
  - Subtle secondary metric
  - Generous spacing, rounded feel

Usage:
    card = StatCard(parent, title="SESSION", primary="12", primary_label="Actions",
                    secondary="98%", secondary_label="Verified")
    card.pack(side="left", padx=4, fill="both", expand=True)

    card.update(primary="15", secondary="100%")
"""

from __future__ import annotations
import tkinter as tk
from .theme import C, F, ThemeManager


class StatCard:
    """
    Compact glass statistics card — reference image 3 aesthetic.
    Soft, rounded, clean. No dense tables.
    """

    def __init__(self,
                 parent: tk.Widget,
                 title: str = "STAT",
                 primary: str = "—",
                 primary_label: str = "",
                 secondary: str = "",
                 secondary_label: str = "",
                 accent_color: str | None = None,
                 min_width: int = 120) -> None:
        self._accent = accent_color or C.BLUE

        # Card surface
        self.frame = tk.Frame(
            parent,
            bg=C.DEPTH_2,
            highlightthickness=1,
            highlightbackground=C.DEPTH_BD_2,
        )

        body = tk.Frame(self.frame, bg=C.DEPTH_2, padx=14, pady=12)
        body.pack(fill="both", expand=True)

        # Title
        tk.Label(body, text=title,
                 font=(F._PRIMARY, F.XS, "bold"),
                 bg=C.DEPTH_2, fg=C.FG_3,
                 anchor="w").pack(fill="x", pady=(0, 8))

        # Separator
        tk.Frame(body, bg=C.DEPTH_BD_2, height=1).pack(fill="x", pady=(0, 8))

        # Primary metric
        self._primary_lbl = tk.Label(body, text=primary,
                                     font=(F._PRIMARY, 14, "bold"),
                                     bg=C.DEPTH_2, fg=C.FG_1,
                                     anchor="w", wraplength=140, justify="left")
        self._primary_lbl.pack(fill="x")

        if primary_label:
            self._primary_sub = tk.Label(body, text=primary_label,
                                         font=(F._FALLBACK, F.XS),
                                         bg=C.DEPTH_2, fg=C.FG_3,
                                         anchor="w")
            self._primary_sub.pack(fill="x")
        else:
            self._primary_sub = None

        # Secondary metric (optional)
        if secondary:
            tk.Frame(body, bg=C.DEPTH_BD_2, height=1).pack(fill="x", pady=(6, 0))
            self._secondary_lbl = tk.Label(body, text=secondary,
                                           font=(F._PRIMARY, 13, "bold"),
                                           bg=C.DEPTH_2, fg=self._accent,
                                           anchor="w", wraplength=140, justify="left")
            self._secondary_lbl.pack(fill="x", pady=(4, 0))

            if secondary_label:
                self._secondary_sub = tk.Label(body, text=secondary_label,
                                               font=(F._FALLBACK, F.XS),
                                               bg=C.DEPTH_2, fg=C.FG_3,
                                               anchor="w")
                self._secondary_sub.pack(fill="x")
            else:
                self._secondary_sub = None
        else:
            self._secondary_lbl = None
            self._secondary_sub = None

        ThemeManager.add_listener(self._on_theme_changed)

    def pack(self, **kwargs) -> None:
        self.frame.pack(**kwargs)

    def grid(self, **kwargs) -> None:
        self.frame.grid(**kwargs)

    def update(self, primary: str = None, secondary: str = None,
               primary_label: str = None, secondary_label: str = None) -> None:
        try:
            if primary is not None:
                self._primary_lbl.configure(text=primary)
            if primary_label is not None and self._primary_sub:
                self._primary_sub.configure(text=primary_label)
            if secondary is not None and self._secondary_lbl:
                self._secondary_lbl.configure(text=secondary)
            if secondary_label is not None and self._secondary_sub:
                self._secondary_sub.configure(text=secondary_label)
        except Exception:
            pass

    def _on_theme_changed(self) -> None:
        try:
            self.frame.configure(bg=C.DEPTH_2, highlightbackground=C.DEPTH_BD_2)
        except Exception:
            pass
