"""
ui/icon_manager.py — HELIOS v5.0 Icon Renderer System
=======================================================
Priority-1 icon source: Segoe Fluent Icons (confirmed available on Windows 10/11)
Priority-2 fallback:    Segoe MDL2 Assets
Priority-3 fallback:    Clean text symbols (no emoji)

Segoe Fluent Icons renders genuine graphical vector icons — speech bubbles,
clocks, monitor outlines, gear wheels — NOT text characters.

The IconRenderer abstracts all icon drawing behind a single interface:
  IconRenderer.draw(canvas, cx, cy, name, size, state, theme)

Navigation rail and other components never know the icon source.

Icon States:
  "idle"    — muted, calm color
  "hover"   — brightened, accent glow
  "pressed" — slightly darker, inset feel
  "active"  — full accent color, ambient glow

Per-icon semantic accent colors (restrained, not neon):
  chat      — cyan   #22D3EE
  history   — violet #A78BFA
  desktop   — blue   #60A5FA
  activity  — teal   #2DD4BF
  settings  — indigo #818CF8
  compact   — blue   #60A5FA
"""

from __future__ import annotations
import sys
import tkinter as tk
from .theme import hex_lerp


# ── Font Detection ─────────────────────────────────────────────────────────────
def _detect_icon_font() -> str:
    if sys.platform != "win32":
        return "Segoe UI Symbol"
    # Both confirmed available on this system
    return "Segoe Fluent Icons"


ICON_FONT     = _detect_icon_font()
ICON_FONT_ALT = "Segoe MDL2 Assets"
ICON_FONT_SYM = "Segoe UI Symbol"


# ── Icon Code Points (Segoe Fluent Icons — visually verified) ─────────────────
class I:
    """
    HELIOS v5.0 Vector Icon Registry.
    Codepoints verified against Segoe Fluent Icons rendering.
    """

    # ── Navigation Rail (graphical, not text-like) ────────────────────────────
    CHAT         = "\uE8BD"  # Speech bubble (graphical)
    HISTORY      = "\uE81C"  # History/clock (graphical)
    DESKTOP      = "\uE770"  # Monitor/screen (graphical)
    DIAGNOSTICS  = "\uE9D9"  # Heartbeat/activity (graphical)
    SETTINGS     = "\uE713"  # Settings gear (graphical)
    MEMORY       = "\uE944"  # Memory/brain
    ROUTING      = "\uE895"  # Route/flow
    MODELS       = "\uE979"  # Model Grid / Cubes (alias for grid)
    INFO         = "\uE946"  # Info badge

    # ── Header & Window Controls ──────────────────────────────────────────────
    HELIOS_AVATAR = "H"       # Rendered on Canvas as styled sphere
    MINIMIZE     = "\uE921"   # Native minimize bar
    MAXIMIZE     = "\uE922"   # Native maximize square
    RESTORE      = "\uE923"   # Native restore
    CLOSE        = "\uE8BB"   # X close
    MENU         = "\uE712"   # Hamburger menu
    COMPACT_ON   = "\uE74C"   # Collapse/compact (responsive layout)
    COMPACT_OFF  = "\uE740"   # Expand back to desktop

    # ── Input / Command Bar ───────────────────────────────────────────────────
    ATTACH       = "\uE710"   # Add / Plus
    CAMERA       = "\uE722"   # Camera
    MIC_IDLE     = "\uE720"   # Microphone
    MIC_LIVE     = "\uE720"   # Recording (different color)
    SEND         = "\uE72A"   # Send arrow
    CLEAR        = "\uE8BB"   # Clear X

    # ── Response Actions ──────────────────────────────────────────────────────
    COPY         = "\uE8C8"   # Copy
    EDIT         = "\uE70F"   # Edit pencil
    DELETE       = "\uE74D"   # Trash
    RETRY        = "\uE72C"   # Refresh/retry
    SAVE         = "\uE74E"   # Save/bookmark
    EXPAND       = "\uE740"   # Expand
    PIN          = "\uE718"   # Pin
    BACK         = "\uE76B"   # Back chevron
    FORWARD      = "\uE76C"   # Forward chevron

    # ── Status & Indicators ───────────────────────────────────────────────────
    DOT_OK       = "\uE73E"   # Check mark
    DOT_WARN     = "\uE7BA"   # Warning triangle
    DOT_ERR      = "\uE783"   # Error X
    DOT_IDLE     = "\uEA3B"   # Circle
    DOT_SPIN     = "\uE72C"   # Spinner

    ERR_ICON     = "\uE7BA"   # Warning triangle
    INFO_ICON    = "\uE946"   # Info badge

    # ── Pipeline ──────────────────────────────────────────────────────────────
    STAGE_WAIT   = "\uEA3B"
    STAGE_RUN    = "\uE72C"
    STAGE_DONE   = "\uE73E"
    STAGE_ERR    = "\uE783"

    PLAN         = "\uE8B8"
    MEMORY_ICON  = "\uE944"
    ROUTE        = "\uE895"
    EXEC         = "\uE768"
    VERIFY       = "\uE73E"
    DONE         = "\uE73E"

    # ── Files ─────────────────────────────────────────────────────────────────
    FILE_DOC     = "\uE8A5"
    FILE_IMG     = "\uEB9F"
    FILE_CODE    = "\uE943"
    FILE_DATA    = "\uE9F9"
    FILE_PDF     = "\uEA90"

    # ── Models ────────────────────────────────────────────────────────────────
    MODEL_LOCAL  = "\uE839"
    MODEL_CLOUD  = "\uE753"
    MODEL_ACTIVE = "\uE768"

    # ── Memory Hierarchy ─────────────────────────────────────────────────────
    L1           = "\uE839"
    L2           = "\uE979"
    L3           = "\uE944"
    L4           = "\uE9D9"

    # ── Search & Nav ──────────────────────────────────────────────────────────
    SEARCH       = "\uE721"
    STAR         = "\uE734"
    STAR_EMPTY   = "\uE735"
    REFRESH      = "\uE72C"
    CHEVRON_R    = "\uE76C"
    CHEVRON_L    = "\uE76B"
    CHEVRON_D    = "\uE70D"
    CHEVRON_U    = "\uE70E"
    TRASH        = "\uE74D"

    # ── Quick Actions ─────────────────────────────────────────────────────────
    NEW_NOTE     = "\uE70F"
    ANALYZE      = "\uE9F9"
    WEB_SEARCH   = "\uE721"
    SCHEDULE     = "\uE787"

    # ── Tags ──────────────────────────────────────────────────────────────────
    TAG_LOCAL    = "\uE839"
    TAG_CLOUD    = "\uE753"
    TAG_FAST     = "\uE768"
    TAG_SMART    = "\uE9A6"
    TAG_PRIVATE  = "\uE72E"


# ── Icon Size Presets ─────────────────────────────────────────────────────────
class IS:
    """Icon size presets (Point sizes for Canvas text rendering)."""
    XS  = 10
    SM  = 12
    MD  = 14
    LG  = 18
    XL  = 24
    NAV = 16   # Navigation rail icon size — optimized for 44px container


# ── Per-Icon Semantic Accent Colors ──────────────────────────────────────────
# Restrained, not neon. Clearly different from each other.
ICON_ACCENTS = {
    "chat":        {"idle": "#1E6A7A", "hover": "#22D3EE", "active": "#22D3EE", "pressed": "#0E5060"},
    "history":     {"idle": "#5B3A8A", "hover": "#A78BFA", "active": "#A78BFA", "pressed": "#3D2060"},
    "desktop":     {"idle": "#1D3A70", "hover": "#60A5FA", "active": "#60A5FA", "pressed": "#122450"},
    "activity":    {"idle": "#1A5050", "hover": "#2DD4BF", "active": "#2DD4BF", "pressed": "#0F3535"},
    "diagnostics": {"idle": "#1A5050", "hover": "#2DD4BF", "active": "#2DD4BF", "pressed": "#0F3535"},
    "settings":    {"idle": "#2D2D60", "hover": "#818CF8", "active": "#818CF8", "pressed": "#1A1A45"},
    "memory":      {"idle": "#2D2D60", "hover": "#818CF8", "active": "#818CF8", "pressed": "#1A1A45"},
    "routing":     {"idle": "#1D3A70", "hover": "#60A5FA", "active": "#60A5FA", "pressed": "#122450"},
    "compact":     {"idle": "#1D3A70", "hover": "#60A5FA", "active": "#60A5FA", "pressed": "#122450"},
    "default":     {"idle": "#374B6A", "hover": "#94A3B8", "active": "#38BDF8", "pressed": "#1A2440"},
}

# Light theme accent colors (more restrained, deeper for contrast)
ICON_ACCENTS_LIGHT = {
    "chat":        {"idle": "#0891B2", "hover": "#0E7490", "active": "#0E7490", "pressed": "#0C6080"},
    "history":     {"idle": "#7C3AED", "hover": "#6D28D9", "active": "#6D28D9", "pressed": "#5B21B6"},
    "desktop":     {"idle": "#2563EB", "hover": "#1D4ED8", "active": "#1D4ED8", "pressed": "#1E40AF"},
    "activity":    {"idle": "#0D9488", "hover": "#0F766E", "active": "#0F766E", "pressed": "#0C5E5A"},
    "diagnostics": {"idle": "#0D9488", "hover": "#0F766E", "active": "#0F766E", "pressed": "#0C5E5A"},
    "settings":    {"idle": "#4F46E5", "hover": "#4338CA", "active": "#4338CA", "pressed": "#3730A3"},
    "memory":      {"idle": "#4F46E5", "hover": "#4338CA", "active": "#4338CA", "pressed": "#3730A3"},
    "routing":     {"idle": "#2563EB", "hover": "#1D4ED8", "active": "#1D4ED8", "pressed": "#1E40AF"},
    "compact":     {"idle": "#2563EB", "hover": "#1D4ED8", "active": "#1D4ED8", "pressed": "#1E40AF"},
    "default":     {"idle": "#64748B", "hover": "#334155", "active": "#2563EB", "pressed": "#1E293B"},
}


# ── Surface Colors by Theme ───────────────────────────────────────────────────
_DARK_SURFACE  = {
    "normal":  "#0F1535",
    "hover":   "#152048",
    "pressed": "#080B20",
    "active":  "#0D1A35",
}
_LIGHT_SURFACE = {
    "normal":  "#EAEFF8",
    "hover":   "#DDE5F4",
    "pressed": "#CDD8EE",
    "active":  "#D8E4F4",
}
_DARK_SHADOWS  = {"light": "#1E2654", "dark": "#020408"}
_LIGHT_SHADOWS = {"light": "#FFFFFF", "dark": "#C0CEDF"}


# ── IconRenderer ──────────────────────────────────────────────────────────────
class IconRenderer:
    """
    Central icon rendering system.

    Usage:
        renderer = IconRenderer(theme="dark")
        renderer.draw_nav_button(canvas, key="chat", state="idle")
        renderer.draw_compact_button(canvas, state="hover", is_compact=False)

    The canvas must be pre-sized (44×44 for nav, 28×28 for compact).
    All draw calls first delete the tag, then redraw.
    """

    def __init__(self, theme: str = "dark") -> None:
        self._theme = theme  # "dark" or "light"

    def set_theme(self, theme: str) -> None:
        self._theme = theme

    def _accents(self, key: str, state: str) -> str:
        """Return the correct accent color for key+state+theme."""
        table = ICON_ACCENTS if self._theme == "dark" else ICON_ACCENTS_LIGHT
        row   = table.get(key, table["default"])
        return row.get(state, row["idle"])

    def _surface(self, state: str) -> str:
        tbl = _DARK_SURFACE if self._theme == "dark" else _LIGHT_SURFACE
        return tbl.get(state, tbl["normal"])

    def _shadows(self) -> dict:
        return _DARK_SHADOWS if self._theme == "dark" else _LIGHT_SHADOWS

    def draw_nav_button(
        self,
        canvas: tk.Canvas,
        key: str,
        glyph: str,
        state: str = "idle",     # idle / hover / pressed / active
        size: int = 44,
        tag: str = "navbtn",
    ) -> None:
        """
        Draw a complete neumorphic navigation button with icon.

        Layers (bottom to top):
          1. outer_shadow (dark oval, bottom-right offset)
          2. light_shadow (lighter oval, top-left offset)
          3. surface (main neumorphic oval)
          4. highlight arc (top-left specular)
          5. ambient glow oval (only in hover/active)
          6. border oval
          7. icon glyph (Segoe Fluent Icons)
          8. active dot indicator
        """
        canvas.delete(tag)
        r    = size // 2 - 3    # inner circle radius
        cx   = size // 2
        cy   = size // 2
        sh   = self._shadows()
        surf = self._surface(state)
        acc  = self._accents(key, state)

        if state == "pressed":
            self._draw_inset(canvas, cx, cy, r, surf, sh, acc, tag)
        elif state == "active":
            self._draw_active(canvas, cx, cy, r, acc, tag)
        elif state == "hover":
            self._draw_hover(canvas, cx, cy, r, surf, sh, acc, tag)
        else:
            self._draw_idle(canvas, cx, cy, r, surf, sh, tag)

        # ── Icon glyph ────────────────────────────────────────────────────────
        icon_color = acc if state in ("hover", "active") else self._accents(key, "idle")
        if state == "active":
            icon_color = acc
        canvas.create_text(
            cx, cy,
            text=glyph,
            font=(ICON_FONT, IS.NAV),
            fill=icon_color,
            tags=tag,
        )

        # ── Active indicator dot ──────────────────────────────────────────────
        if state == "active":
            dot_y = cy + r + 4
            canvas.create_oval(
                cx - 3, dot_y - 3,
                cx + 3, dot_y + 3,
                fill=acc, outline="", tags=tag,
            )

    def _draw_idle(self, canvas, cx, cy, r, surf, sh, tag):
        # Outer shadow (bottom-right offset)
        canvas.create_oval(
            cx - r + 2, cy - r + 2, cx + r + 4, cy + r + 4,
            fill=sh["dark"], outline="", tags=tag,
        )
        # Light shadow (top-left offset)
        canvas.create_oval(
            cx - r - 4, cy - r - 4, cx + r - 2, cy + r - 2,
            fill=sh["light"], outline="", tags=tag,
        )
        # Main surface
        canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=surf, outline="", tags=tag,
        )
        # Specular highlight arc (top-left)
        hl = hex_lerp(surf, sh["light"], 0.5)
        canvas.create_arc(
            cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3,
            start=45, extent=150,
            style="arc", outline=hl, width=1, tags=tag,
        )

    def _draw_hover(self, canvas, cx, cy, r, surf, sh, acc, tag):
        # Ambient glow (soft outer ring)
        glow = hex_lerp(acc, "#000000", 0.75)
        canvas.create_oval(
            cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5,
            fill=glow, outline="", tags=tag,
        )
        # Slightly larger outer shadow (elevation increase)
        canvas.create_oval(
            cx - r + 2, cy - r + 2, cx + r + 5, cy + r + 5,
            fill=sh["dark"], outline="", tags=tag,
        )
        # Light shadow
        canvas.create_oval(
            cx - r - 5, cy - r - 5, cx + r - 2, cy + r - 2,
            fill=sh["light"], outline="", tags=tag,
        )
        # Brighter surface
        canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=hex_lerp(surf, sh["light"], 0.15), outline="", tags=tag,
        )
        # Accent border ring
        canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=acc, width=1, tags=tag,
        )
        # Specular
        hl = hex_lerp(acc, "#FFFFFF", 0.3)
        canvas.create_arc(
            cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3,
            start=45, extent=120,
            style="arc", outline=hl, width=1, tags=tag,
        )

    def _draw_pressed(self, canvas, cx, cy, r, surf, sh, acc, tag):
        # No outer shadow (inset feel)
        darker = hex_lerp(surf, "#000000", 0.25)
        canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=darker, outline=sh["dark"], width=1, tags=tag,
        )
        # Inner shadow at top-left (inset illusion)
        canvas.create_arc(
            cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2,
            start=45, extent=180,
            style="arc", outline=sh["dark"], width=2, tags=tag,
        )
        # Inner highlight at bottom-right
        canvas.create_arc(
            cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2,
            start=225, extent=180,
            style="arc", outline=sh["light"], width=1, tags=tag,
        )

    def _draw_inset(self, canvas, cx, cy, r, surf, sh, acc, tag):
        self._draw_pressed(canvas, cx, cy, r, surf, sh, acc, tag)

    def _draw_active(self, canvas, cx, cy, r, acc, tag):
        # Ambient glow ring
        glow_outer = hex_lerp(acc, "#000000", 0.82)
        glow_inner = hex_lerp(acc, "#000000", 0.72)
        canvas.create_oval(
            cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6,
            fill=glow_outer, outline="", tags=tag,
        )
        canvas.create_oval(
            cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2,
            fill=glow_inner, outline="", tags=tag,
        )
        # Surface with accent tint
        surface = hex_lerp(acc, "#080B1A", 0.80)
        canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=surface, outline=acc, width=1, tags=tag,
        )
        # Specular on active
        hl = hex_lerp(acc, "#FFFFFF", 0.35)
        canvas.create_arc(
            cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3,
            start=50, extent=110,
            style="arc", outline=hl, width=1, tags=tag,
        )

    # ── Compact Toggle Button ─────────────────────────────────────────────────
    def draw_compact_button(
        self,
        canvas: tk.Canvas,
        state: str = "idle",
        is_compact: bool = False,
        size: int = 28,
        tag: str = "compact_btn",
    ) -> None:
        """Draw the top-right compact/desktop view toggle button."""
        canvas.delete(tag)
        r  = size // 2 - 2
        cx = size // 2
        cy = size // 2
        sh = self._shadows()

        key  = "compact"
        surf = self._surface(state)
        acc  = self._accents(key, state)

        if state == "pressed":
            self._draw_inset(canvas, cx, cy, r, surf, sh, acc, tag)
        elif state == "hover":
            self._draw_hover(canvas, cx, cy, r, surf, sh, acc, tag)
        else:
            self._draw_idle(canvas, cx, cy, r, surf, sh, tag)
            if is_compact:
                canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                   outline=acc, width=1, tags=tag)

        glyph = I.COMPACT_ON if not is_compact else I.COMPACT_OFF
        icon_color = acc if (state in ("hover", "active") or is_compact) else self._accents(key, "idle")
        canvas.create_text(
            cx, cy,
            text=glyph,
            font=(ICON_FONT, 11),
            fill=icon_color,
            tags=tag,
        )

    # ── Generic Icon Draw (for input bar tools etc.) ──────────────────────────
    def draw_tool_button(
        self,
        canvas: tk.Canvas,
        glyph: str,
        state: str = "idle",
        accent_color: str = "#38BDF8",
        size: int = 32,
        tag: str = "toolbtn",
        bg_color: str = "#0F1535",
    ) -> None:
        """Draw a small circular tool button (input bar: attach, mic, etc.)."""
        canvas.delete(tag)
        r  = size // 2 - 2
        cx = size // 2
        cy = size // 2
        sh = self._shadows()

        if state == "hover":
            glow = hex_lerp(accent_color, "#000000", 0.8)
            canvas.create_oval(cx-r-3, cy-r-3, cx+r+3, cy+r+3,
                               fill=glow, outline="", tags=tag)

        canvas.create_oval(
            cx - r + 1, cy - r + 1, cx + r + 1, cy + r + 1,
            fill=sh["dark"], outline="", tags=tag,
        )
        surf = hex_lerp(bg_color, sh["light"], 0.08) if state == "hover" else bg_color
        canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=surf,
            outline=accent_color if state == "hover" else hex_lerp(bg_color, "#FFFFFF", 0.1),
            width=1, tags=tag,
        )
        canvas.create_arc(
            cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2,
            start=45, extent=150, style="arc",
            outline=hex_lerp(surf, "#FFFFFF", 0.2), width=1, tags=tag,
        )
        icon_c = accent_color if state == "hover" else hex_lerp(accent_color, "#000000", 0.3)
        canvas.create_text(
            cx, cy, text=glyph,
            font=(ICON_FONT, 11),
            fill=icon_c, tags=tag,
        )


# ── Icon State Color Map (legacy compat) ───────────────────────────────────────
ICON_STATES = {
    "normal":   "NAV_ICON",
    "hover":    "FG_1",
    "active":   "NAV_ICON_A",
    "disabled": "FG_4",
}
