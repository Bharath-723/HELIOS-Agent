"""
ui/product_card.py — HELIOS Commerce Product Card
==================================================
Premium glass product card for commerce results.

Design:
  Glass DEPTH_2 surface
  Left blue accent strip
  Product name (large)
  Price (prominent, cyan)
  Source + verified badge
  View / Add to Cart buttons

Usage:
    card = ProductCard(parent, product_dict, on_view=..., on_cart=...)
    card.pack(fill="x", padx=14, pady=4)
"""

from __future__ import annotations
import tkinter as tk
from datetime import datetime
from .theme import C, F, S, ThemeManager


class ProductCard:
    """
    Glass product card — restrained premium commerce tile.
    Does NOT look like a bright ecommerce widget.
    """

    def __init__(self,
                 parent: tk.Widget,
                 product: dict,
                 on_view: callable = None,
                 on_cart: callable = None) -> None:

        name     = product.get("name", "Product")
        price    = product.get("price", "")
        source   = product.get("source", "")
        verified = product.get("verified", False)
        rating   = product.get("rating", "")
        desc     = product.get("description", "")

        # Shadow frame
        self._shadow = tk.Frame(parent, bg=C.SHADOW_SM)
        self.frame   = self._shadow

        # Card
        self._card = tk.Frame(
            self._shadow,
            bg=C.DEPTH_2,
            highlightthickness=1,
            highlightbackground=C.DEPTH_BD_2,
        )
        self._card.pack(fill="both", expand=True, padx=(0,1), pady=(0,1))

        # Top highlight
        tk.Frame(self._card, bg=C.DEPTH_BD_3, height=1).pack(fill="x")

        # Row: accent + body
        row = tk.Frame(self._card, bg=C.DEPTH_2)
        row.pack(fill="both", expand=True)

        tk.Frame(row, bg=C.BLUE, width=3).pack(side="left", fill="y")

        body = tk.Frame(row, bg=C.DEPTH_2, padx=14, pady=10)
        body.pack(fill="both", expand=True)

        # Badge: PRODUCT label
        tag_row = tk.Frame(body, bg=C.DEPTH_2)
        tag_row.pack(fill="x", pady=(0, 6))
        tk.Label(tag_row, text="  PRODUCT  ",
                 font=(F._FALLBACK, F.XS, "bold"),
                 bg=C.BLUE_DIM, fg=C.BLUE_L,
                 padx=4, pady=1).pack(side="left")

        if verified:
            tk.Label(tag_row, text="  ✓ VERIFIED  ",
                     font=(F._FALLBACK, F.XS, "bold"),
                     bg=C.OK_D, fg=C.OK_L,
                     padx=4, pady=1).pack(side="left", padx=(4, 0))

        # Product name
        tk.Label(body, text=name,
                 font=(F._PRIMARY, F.LG, "bold"),
                 bg=C.DEPTH_2, fg=C.FG_1,
                 anchor="w", wraplength=380, justify="left").pack(fill="x")

        # Description (if provided)
        if desc:
            tk.Label(body, text=desc,
                     font=(F._FALLBACK, F.XS),
                     bg=C.DEPTH_2, fg=C.FG_3,
                     anchor="w", wraplength=380, justify="left").pack(fill="x", pady=(2, 0))

        # Price row
        price_row = tk.Frame(body, bg=C.DEPTH_2)
        price_row.pack(fill="x", pady=(8, 0))

        if price:
            tk.Label(price_row, text=price,
                     font=(F._PRIMARY, 18, "bold"),
                     bg=C.DEPTH_2, fg=C.CYAN).pack(side="left")

        if rating:
            tk.Label(price_row, text=f"  ★ {rating}",
                     font=(F._FALLBACK, F.SM),
                     bg=C.DEPTH_2, fg=C.FG_3).pack(side="left", padx=8)

        # Source
        if source:
            src_row = tk.Frame(body, bg=C.DEPTH_2)
            src_row.pack(fill="x", pady=(4, 0))
            tk.Label(src_row, text=source,
                     font=(F._FALLBACK, F.XS),
                     bg=C.DEPTH_2, fg=C.FG_3).pack(side="left")

        # Action buttons
        btn_row = tk.Frame(body, bg=C.DEPTH_2)
        btn_row.pack(fill="x", pady=(10, 2))

        def _btn(parent, text, bg, fg, command):
            b = tk.Button(parent, text=text,
                          font=(F._FALLBACK, F.SM),
                          bg=bg, fg=fg,
                          activebackground=C.BG_HOVER, activeforeground=fg,
                          relief="flat", bd=0,
                          padx=12, pady=5,
                          cursor="hand2",
                          command=command or (lambda: None))
            return b

        _btn(btn_row, "  View  ", C.DEPTH_3, C.FG_2,
             on_view).pack(side="left", padx=(0, 8))
        _btn(btn_row, "  Add to Cart  ", C.BLUE_DIM, C.BLUE_L,
             on_cart).pack(side="left")

        ThemeManager.add_listener(self._on_theme_changed)

    def pack(self, **kwargs) -> None:
        self._shadow.pack(**kwargs)

    def _on_theme_changed(self) -> None:
        try:
            self._shadow.configure(bg=C.SHADOW_SM)
            self._card.configure(bg=C.DEPTH_2, highlightbackground=C.DEPTH_BD_2)
        except Exception:
            pass
