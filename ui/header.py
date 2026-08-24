"""
ui/header.py — HELIOS v5.0 Material Glass Header
=================================================
Full Canvas-based header with:
  - Layered 5-sphere HELIOS avatar (shadow → glow → glass ring → gradient sphere → specular → H)
  - Title block with glass model badge
  - Status indicator
  - Window controls (Segoe Fluent Icons)
  - Top-right compact/desktop view toggle (IconRenderer)
"""

from __future__ import annotations
import tkinter as tk
from .theme import C, F, S, ThemeManager, hex_lerp
from .icon_manager import I, IconRenderer, ICON_FONT

# ── Dark theme header palette ─────────────────────────────────────────────────
_D = {
    "bg":        "#070A1C",
    "bg2":       "#0B1028",
    "border":    "#1A2655",
    "title":     "#E8EFF8",
    "subtitle":  "#6A7E9A",
    "badge_bg":  "#0C2338",
    "badge_fg":  "#22D3EE",
    "dot_ok":    "#10B981",
    "dot_warn":  "#F59E0B",
    "wc_fg":     "#4A5B7A",
    "wc_hover":  "#8899BB",
    "wc_close":  "#DC2626",
}
# ── Light theme header palette ────────────────────────────────────────────────
_L = {
    "bg":        "#F0F5FF",
    "bg2":       "#E8EFF8",
    "border":    "#C8D5E8",
    "title":     "#1E293B",
    "subtitle":  "#64748B",
    "badge_bg":  "#DBEAFE",
    "badge_fg":  "#2563EB",
    "dot_ok":    "#059669",
    "dot_warn":  "#D97706",
    "wc_fg":     "#94A3B8",
    "wc_hover":  "#334155",
    "wc_close":  "#DC2626",
}


def _p() -> dict:
    return _L if ThemeManager.get_mode() == "light" else _D


class Header:
    """Top header bar — full Canvas rendering, layered avatar, material controls."""

    H = 60    # Header height in pixels

    def __init__(
        self,
        parent: tk.Widget,
        on_close:         callable,
        on_minimize:      callable,
        on_settings:      callable,
        on_drag_start:    callable,
        on_drag_do:       callable,
        on_drag_end:      callable,
        on_maximize:      callable = None,
        on_auto_toggle:   callable = None,
        on_compact_toggle: callable = None,
    ) -> None:
        self._on_close          = on_close
        self._on_minimize       = on_minimize
        self._on_maximize       = on_maximize
        self._on_settings       = on_settings
        self._on_auto_toggle    = on_auto_toggle
        self._on_compact_toggle = on_compact_toggle

        self._is_compact   = False
        self._is_maximized = False
        self._renderer     = IconRenderer(theme=ThemeManager.get_mode())

        # Outer frame (sets height)
        self.frame = tk.Frame(parent, bg=_p()["bg"], height=self.H)
        self.frame.pack_propagate(False)

        self._build(on_drag_start, on_drag_do, on_drag_end)
        ThemeManager.add_listener(self._on_theme_changed)

    # ─────────────────────────────────────────────────────────────────────────
    def _build(self, drag_start, drag_do, drag_end) -> None:
        p = _p()

        # Bottom glass border
        self._border_f = tk.Frame(self.frame, bg=p["border"], height=1)
        self._border_f.pack(fill="x", side="bottom")

        # ── Avatar (Canvas, 48×48) ────────────────────────────────────────────
        self.av = tk.Canvas(
            self.frame, width=48, height=48,
            bg=p["bg"], highlightthickness=0,
        )
        self.av.pack(side="left", padx=(12, 8), pady=6)
        self._draw_avatar()

        # Drag bindings on avatar
        self.av.bind("<Button-1>",       drag_start)
        self.av.bind("<B1-Motion>",       drag_do)
        self.av.bind("<ButtonRelease-1>", drag_end)

        # ── Title block ───────────────────────────────────────────────────────
        self._tf = tk.Frame(self.frame, bg=p["bg"])
        self._tf.pack(side="left", fill="y", pady=10)

        self._title_row = tk.Frame(self._tf, bg=p["bg"])
        self._title_row.pack(anchor="w")

        self._lbl_title = tk.Label(
            self._title_row, text="HELIOS",
            font=("Segoe UI Variable Display", 13, "bold"),
            bg=p["bg"], fg=p["title"],
        )
        self._lbl_title.pack(side="left")

        # Glass model badge
        self._badge = tk.Label(
            self._title_row, text="  LOCAL AI  ",
            font=("Segoe UI", 8, "bold"),
            bg=p["badge_bg"], fg=p["badge_fg"],
            padx=4, pady=1,
        )
        self._badge.pack(side="left", padx=(8, 0))

        self._status_row = tk.Frame(self._tf, bg=p["bg"])
        self._status_row.pack(anchor="w", pady=(2, 0))

        self._dot_lbl = tk.Label(
            self._status_row, text="●",
            font=("Segoe UI", 8),
            bg=p["bg"], fg=p["dot_ok"],
        )
        self._dot_lbl.pack(side="left", padx=(0, 4))

        self._status_lbl = tk.Label(
            self._status_row,
            text="Gemma 3 4B · Privacy Guard Active",
            font=("Segoe UI", 9),
            bg=p["bg"], fg=p["subtitle"],
        )
        self._status_lbl.pack(side="left")

        # ── Window controls (right side) ──────────────────────────────────────
        self._ctrl = tk.Frame(self.frame, bg=p["bg"])
        self._ctrl.pack(side="right", padx=(0, 10))

        # Compact toggle
        self._compact_cv = tk.Canvas(
            self._ctrl, width=28, height=28,
            bg=p["bg"], highlightthickness=0, cursor="hand2",
        )
        self._compact_cv.pack(side="left", padx=(0, 8))
        self._draw_compact_btn("idle")
        self._bind_compact()

        # Min / Max / Close
        self._min_cv  = self._make_wc_button(self._ctrl, I.MINIMIZE, self._on_minimize)
        if self._on_maximize:
            self._max_cv = self._make_wc_button(self._ctrl, I.MAXIMIZE, self._on_maximize)
        self._close_cv = self._make_wc_button(self._ctrl, I.CLOSE, self._on_close, is_close=True)

        # ── Drag bindings ─────────────────────────────────────────────────────
        drag_targets = [
            self.frame, self._tf, self._title_row, self._status_row,
            self._lbl_title, self._status_lbl,
        ]
        for w in drag_targets:
            w.bind("<Button-1>",       drag_start)
            w.bind("<B1-Motion>",       drag_do)
            w.bind("<ButtonRelease-1>", drag_end)

    # ── Avatar drawing ────────────────────────────────────────────────────────
    def _draw_avatar(self) -> None:
        """Draw 5-layer material glass sphere avatar."""
        av = self.av
        av.delete("all")
        p  = _p()
        cx, cy, r = 24, 24, 20

        # Layer 1: outer shadow (dark, bottom-right)
        av.create_oval(cx-r+3, cy-r+3, cx+r+5, cy+r+5,
                       fill="#010204", outline="", tags="avatar")
        # Layer 2: ambient glow ring (blue)
        glow = "#0A1840" if ThemeManager.get_mode() == "dark" else "#C8D8F0"
        av.create_oval(cx-r-2, cy-r-2, cx+r+2, cy+r+2,
                       fill=glow, outline="", tags="avatar")
        # Layer 3: glass ring border
        ring_c = "#2563EB" if ThemeManager.get_mode() == "dark" else "#93C5FD"
        av.create_oval(cx-r, cy-r, cx+r, cy+r,
                       fill="#1A3A8A" if ThemeManager.get_mode() == "dark" else "#DBEAFE",
                       outline=ring_c, width=1.5, tags="avatar")
        # Layer 4: gradient inner sphere (3 concentric ovals, light→dark top→bottom)
        colors = [
            ("#1E3A8A", "#0F2060"),   # outer
            ("#1A4A9E", "#0E2870"),   # mid
            ("#2055B0", "#1035A0"),   # inner
        ]
        if ThemeManager.get_mode() == "light":
            colors = [
                ("#93C5FD", "#BFDBFE"),
                ("#60A5FA", "#93C5FD"),
                ("#3B82F6", "#60A5FA"),
            ]
        for i, (c1, c2) in enumerate(colors):
            ir = r - 3 - i * 2
            av.create_oval(cx-ir, cy-ir, cx+ir, cy+ir,
                           fill=c1, outline="", tags="avatar")

        # Layer 5: specular highlight (top-left)
        av.create_arc(cx-r+6, cy-r+6, cx+r-12, cy+r-12,
                      start=60, extent=80, style="arc",
                      outline="#AACCFF" if ThemeManager.get_mode() == "dark" else "#FFFFFF",
                      width=2, tags="avatar")

        # Layer 6: H lettermark
        h_color = "#E8F0FF" if ThemeManager.get_mode() == "dark" else "#1E40AF"
        av.create_text(cx, cy+1, text="H",
                       font=("Segoe UI Variable Display", 12, "bold"),
                       fill=h_color, tags="avatar")

    def _on_avatar_hover(self, enter: bool) -> None:
        """Subtle illumination increase on avatar hover."""
        # We just slightly redraw with brighter specular on enter
        self._draw_avatar()

    # ── Compact toggle button ─────────────────────────────────────────────────
    def _draw_compact_btn(self, state: str = "idle") -> None:
        self._renderer.set_theme(ThemeManager.get_mode())
        self._renderer.draw_compact_button(
            self._compact_cv,
            state=state,
            is_compact=self._is_compact,
            size=28, tag="compact_btn",
        )

    def _bind_compact(self) -> None:
        cv = self._compact_cv

        def _click(e):
            self._draw_compact_btn("pressed")
            if self._on_compact_toggle:
                self._on_compact_toggle()
            cv.after(150, lambda: self._draw_compact_btn("idle"))

        cv.bind("<Enter>",          lambda e: self._draw_compact_btn("hover"))
        cv.bind("<Leave>",          lambda e: self._draw_compact_btn("idle"))
        cv.bind("<Button-1>",       lambda e: self._draw_compact_btn("pressed"))
        cv.bind("<ButtonRelease-1>", _click)

    # ── Window control buttons ────────────────────────────────────────────────
    def _make_wc_button(
        self, parent: tk.Widget,
        glyph: str, command: callable,
        is_close: bool = False,
    ) -> tk.Canvas:
        p  = _p()
        size = 26
        cv = tk.Canvas(parent, width=size, height=size,
                       bg=p["bg"], highlightthickness=0, cursor="hand2")
        cv.pack(side="left", padx=2)

        def _draw(state: str = "normal") -> None:
            cv.delete("all")
            if state == "hover":
                bg  = "#DC2626" if is_close else p["bg2"]
                fg  = "#FFFFFF"
                cv.create_oval(2, 2, size-2, size-2, fill=bg, outline="")
            else:
                fg = p["wc_close"] if is_close else p["wc_fg"]
            cv.create_text(
                size // 2, size // 2,
                text=glyph,
                font=(ICON_FONT, 10),
                fill=fg,
            )

        _draw("normal")
        cv.bind("<Enter>",          lambda e: _draw("hover"))
        cv.bind("<Leave>",          lambda e: _draw("normal"))
        cv.bind("<ButtonRelease-1>", lambda e: command())
        return cv

    # ── Public API ────────────────────────────────────────────────────────────
    def set_compact_state(self, is_compact: bool) -> None:
        self._is_compact = is_compact
        self._draw_compact_btn("idle")

    def set_maximized_state(self, is_maximized: bool) -> None:
        self._is_maximized = is_maximized
        if hasattr(self, "_max_cv"):
            glyph = I.RESTORE if is_maximized else I.MAXIMIZE
            self._max_cv.delete("all")
            p = _p()
            self._max_cv.create_text(
                13, 13, text=glyph,
                font=(ICON_FONT, 10), fill=p["wc_fg"],
            )

    def set_status(self, text: str, dot_color: str = None) -> None:
        try:
            self._status_lbl.configure(text=text)
            if dot_color:
                self._dot_lbl.configure(fg=dot_color)
        except Exception:
            pass

    def set_model_status(self, model: str, mode: str = None, state: str = "Ready") -> None:
        self.set_status(f"{model} · Privacy Guard Active")

    def set_auto_route_state(self, state: bool | str) -> None:
        try:
            mode_str = "AUTO" if bool(state) else "MANUAL"
            self._badge.configure(text=f"LOCAL AI ({mode_str})")
        except Exception:
            pass

    # ── Compatibility aliases (for helios_popup.py backward-compat) ──────────
    @property
    def status_lbl(self) -> tk.Label:
        return self._status_lbl

    @property
    def avatar_cv(self) -> tk.Canvas:
        return self.av

    def get_avatar_info(self) -> tuple:
        return (self.av, 0)

    # ── Theme change ──────────────────────────────────────────────────────────
    def _on_theme_changed(self) -> None:
        self._renderer.set_theme(ThemeManager.get_mode())
        p = _p()
        try:
            self.frame.configure(bg=p["bg"])
            self._border_f.configure(bg=p["border"])
            self.av.configure(bg=p["bg"])
            self._draw_avatar()
            self._tf.configure(bg=p["bg"])
            self._title_row.configure(bg=p["bg"])
            self._lbl_title.configure(bg=p["bg"], fg=p["title"])
            self._badge.configure(bg=p["badge_bg"], fg=p["badge_fg"])
            self._status_row.configure(bg=p["bg"])
            self._dot_lbl.configure(bg=p["bg"], fg=p["dot_ok"])
            self._status_lbl.configure(bg=p["bg"], fg=p["subtitle"])
            self._ctrl.configure(bg=p["bg"])
            self._compact_cv.configure(bg=p["bg"])
            self._draw_compact_btn("idle")
            for cv in [self._min_cv]:
                cv.configure(bg=p["bg"])
            if hasattr(self, "_max_cv"):
                self._max_cv.configure(bg=p["bg"])
            self._close_cv.configure(bg=p["bg"])
        except Exception:
            pass
