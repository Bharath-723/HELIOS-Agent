"""
ui/navigation_rail.py — HELIOS v5.0 Material Navigation Rail
=============================================================
Full Canvas-based navigation with layered neumorphic depth.

Design principles:
  - Every icon is a physical object on a raised neumorphic surface
  - Segoe Fluent Icons provides graphical vector icons (not text/emoji)
  - 5 interaction states: IDLE / HOVER / PRESSED / ACTIVE / DISABLED
  - No layout shift on any state change
  - All drawing is Canvas-only — no tk.Frame/tk.Label
  - Material glass tooltip (no root.lift())
  - Responsive: collapses to icon-only in compact mode

Visual anatomy per button:
  Layer 1: outer dark shadow (bottom-right offset)
  Layer 2: light shadow (top-left offset)
  Layer 3: ambient glow oval (hover/active only)
  Layer 4: main neumorphic surface oval
  Layer 5: specular arc highlight (top-left)
  Layer 6: accent border ring (hover/active)
  Layer 7: Segoe Fluent icon glyph
  Layer 8: active state dot indicator
"""

from __future__ import annotations
import tkinter as tk
from .theme import C, F, ThemeManager, hex_lerp
from .icon_manager import I, IconRenderer, ICON_FONT

# ── Color constants (pre-resolved for speed — updated on theme change) ────────
_BG_DARK   = "#070A1C"
_BG_LIGHT  = "#EDF1F8"


# ── Navigation items ──────────────────────────────────────────────────────────
_NAV_ITEMS = [
    ("chat",        I.CHAT,        "Chat"),
    ("history",     I.HISTORY,     "History"),
    ("desktop",     I.DESKTOP,     "Desktop"),
    ("diagnostics", I.DIAGNOSTICS, "Activity"),
    ("settings",    I.SETTINGS,    "Settings"),
]


class _GlassTooltip:
    """
    In-window relative tooltip — no Toplevel creation to prevent orphaned windows.
    """
    _instance: "_GlassTooltip | None" = None

    def __init__(self, root: tk.Widget) -> None:
        self._root = root
        self._lbl_frame: tk.Frame | None = None

    @classmethod
    def get(cls, root: tk.Widget) -> "_GlassTooltip":
        if cls._instance is None:
            cls._instance = cls(root)
        return cls._instance

    def show(self, text: str, x: int, y: int) -> None:
        self.hide()
        theme = ThemeManager.get_mode()
        bg   = "#0F1535" if theme == "dark" else "#F0F5FF"
        fg   = "#E0E8FF" if theme == "dark" else "#1E293B"
        bd   = "#2A3878" if theme == "dark" else "#B0C0DC"

        try:
            self._lbl_frame = tk.Frame(self._root, bg=bd, padx=1, pady=1)
            inner = tk.Frame(self._lbl_frame, bg=bg, padx=8, pady=4)
            inner.pack(fill="both", expand=True)
            tk.Label(inner, text=text, font=("Segoe UI", 9), bg=bg, fg=fg).pack()

            root_x = self._root.winfo_rootx()
            root_y = self._root.winfo_rooty()
            rx = x - root_x if root_x > 0 else 60
            ry = y - root_y if root_y > 0 else 100
            self._lbl_frame.place(x=max(10, rx), y=max(10, ry))
            self._lbl_frame.lift()
        except Exception:
            pass

    def hide(self) -> None:
        if self._lbl_frame:
            try:
                self._lbl_frame.destroy()
            except Exception:
                pass
            self._lbl_frame = None


class NavigationRail:
    """
    Floating glass navigation rail with 5 neumorphic Canvas buttons.

    All visuals drawn on Canvas — genuine neumorphic depth with shadow layers,
    specular highlights, ambient glow, and Segoe Fluent icon glyphs.
    """

    BTN_SIZE  = 44    # Icon button canvas size (px)
    BTN_PAD_V = 10    # Vertical padding between buttons
    BTN_PAD_H = 6     # Horizontal padding (centers 44px button in 56px rail)
    RAIL_W    = 56    # Rail width

    def __init__(self, parent: tk.Widget, on_nav: callable,
                 tooltip_parent: tk.Widget = None) -> None:
        self._on_nav        = on_nav
        self._tooltip_root  = tooltip_parent
        self._active_key    = "chat"
        self._buttons: dict[str, dict] = {}
        self._renderer      = IconRenderer(theme=ThemeManager.get_mode())

        # Rail background canvas
        self.frame = tk.Frame(parent, bg=self._rail_bg(), width=self.RAIL_W)
        self.frame.pack_propagate(False)

        self._build()
        ThemeManager.add_listener(self._on_theme_changed)

    # ── Rail background color ─────────────────────────────────────────────────
    def _rail_bg(self) -> str:
        if ThemeManager.get_mode() == "light":
            return _BG_LIGHT
        return _BG_DARK

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # Right border line (glass edge)
        self._border_cv = tk.Canvas(
            self.frame, width=1,
            bg=self._rail_bg(), highlightthickness=0,
        )
        self._border_cv.pack(side="right", fill="y")
        self._draw_rail_border()

        # Vertical spacer at top
        tk.Frame(self.frame, bg=self._rail_bg(), height=16).pack()

        # Build each nav button
        for key, glyph, label in _NAV_ITEMS:
            self._make_button(key, glyph, label)

    def _draw_rail_border(self) -> None:
        """Draw the right-edge glass border line on the rail."""
        if ThemeManager.get_mode() == "dark":
            color = "#1A2655"
        else:
            color = "#C8D5E8"
        self._border_cv.configure(bg=color)

    # ── Button construction ───────────────────────────────────────────────────
    def _make_button(self, key: str, glyph: str, label: str) -> None:
        bg = self._rail_bg()
        cv = tk.Canvas(
            self.frame,
            width=self.BTN_SIZE,
            height=self.BTN_SIZE,
            bg=bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        cv.pack(pady=self.BTN_PAD_V, padx=self.BTN_PAD_H)

        tooltip: _GlassTooltip | None = None
        if self._tooltip_root:
            tooltip = _GlassTooltip.get(self._tooltip_root)

        def _state() -> str:
            return "active" if self._active_key == key else "idle"

        def _draw(state: str = None) -> None:
            s = state if state is not None else _state()
            self._renderer.draw_nav_button(
                cv, key=key, glyph=glyph,
                state=s, size=self.BTN_SIZE, tag="navbtn",
            )

        def _on_enter(e) -> None:
            if self._active_key != key:
                _draw("hover")
            # Show tooltip to the right of rail
            if tooltip:
                x = cv.winfo_rootx() + self.RAIL_W + 4
                y = cv.winfo_rooty() + self.BTN_SIZE // 2 - 14
                tooltip.show(label, x, y)

        def _on_leave(e) -> None:
            _draw()    # restore idle or active
            if tooltip:
                tooltip.hide()

        def _on_press(e) -> None:
            if self._active_key != key:
                _draw("pressed")

        def _on_release(e) -> None:
            if tooltip:
                tooltip.hide()
            self.set_active(key)
            if self._on_nav:
                self._on_nav(key)

        cv.bind("<Enter>",          _on_enter)
        cv.bind("<Leave>",          _on_leave)
        cv.bind("<Button-1>",       _on_press)
        cv.bind("<ButtonRelease-1>", _on_release)

        self._buttons[key] = {"cv": cv, "draw": _draw, "glyph": glyph}
        _draw()

    # ── Public API ────────────────────────────────────────────────────────────
    def set_active(self, key: str) -> None:
        self._active_key = key
        for k, btn in self._buttons.items():
            btn["draw"]()

    def set_developer_mode(self, enabled: bool) -> None:
        pass   # Reserved

    def collapse(self) -> None:
        """Hide rail (compact mode)."""
        self.frame.pack_forget()

    def expand(self) -> None:
        """Show rail (desktop mode)."""
        self.frame.pack(side="left", fill="y")

    # ── Theme change ──────────────────────────────────────────────────────────
    def _on_theme_changed(self) -> None:
        mode = ThemeManager.get_mode()
        self._renderer.set_theme(mode)
        bg = self._rail_bg()
        self.frame.configure(bg=bg)
        self._draw_rail_border()
        for btn in self._buttons.values():
            btn["cv"].configure(bg=bg)
            btn["draw"]()
