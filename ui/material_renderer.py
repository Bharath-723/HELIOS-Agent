"""
ui/material_renderer.py — HELIOS Canvas Drawing Primitives
===========================================================
Low-level Canvas drawing helpers for the material glass/neumorphic system.

Every visual surface in HELIOS v5.0 uses Canvas drawing.
No tk.Frame background color simulation.

Primitives:
  draw_shadow()          — multi-layer soft shadow behind a rect
  draw_glass_roundrect() — glass surface (gradient-simulated translucency)
  draw_specular_arc()    — top-left specular highlight
  draw_neu_surface()     — neumorphic raised/inset surface
  draw_ambient_glow()    — colored halo glow around a region
  draw_icon_button()     — complete neumorphic icon button draw

All functions operate on an existing tk.Canvas and return tag strings
for selective canvas.delete() on redraw.
"""

from __future__ import annotations
import tkinter as tk
from .theme import hex_lerp


def _hex_rgb(color: str) -> tuple[int, int, int]:
    """Parse #RRGGBB to (r, g, b)."""
    try:
        return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    except Exception:
        return 8, 11, 26


def _blend(c1: str, c2: str, t: float) -> str:
    """Linear interpolate two hex colors."""
    return hex_lerp(c1, c2, max(0.0, min(1.0, t)))


# ── Shadow ────────────────────────────────────────────────────────────────────
def draw_shadow(
    canvas: tk.Canvas,
    x1: int, y1: int, x2: int, y2: int,
    radius: int = 10,
    shadow_color: str = "#020408",
    bg_color: str = "#080B1A",
    layers: int = 8,
    tag: str = "shadow",
) -> None:
    """
    Multi-layer soft shadow — approximates Gaussian blur via concentric ovals
    that blend from shadow_color (center) → bg_color (edge).

    Draws BEHIND the card, slightly expanded and offset down-right.
    """
    canvas.delete(tag)
    offset_x = 3
    offset_y = 5
    expand   = layers + 2

    sx1 = x1 - expand + offset_x
    sy1 = y1 - expand + offset_y
    sx2 = x2 + expand + offset_x
    sy2 = y2 + expand + offset_y

    for i in range(layers, 0, -1):
        t      = (layers - i) / layers          # 0 at outermost, 1 at innermost
        t_sq   = t * t                           # quadratic falloff (softer)
        color  = _blend(bg_color, shadow_color, t_sq * 0.7)
        shrink = i * 2
        canvas.create_oval(
            sx1 + shrink, sy1 + shrink,
            sx2 - shrink, sy2 - shrink,
            fill=color, outline="",
            tags=tag,
        )


def draw_contact_shadow(
    canvas: tk.Canvas,
    x1: int, y1: int, x2: int, y2: int,
    shadow_color: str = "#020408",
    bg_color: str = "#080B1A",
    tag: str = "contact_shadow",
) -> None:
    """Tight contact shadow — thin dark strip just below the card bottom."""
    canvas.delete(tag)
    cx = (x1 + x2) // 2
    w  = (x2 - x1) * 0.6
    for i, alpha in enumerate([0.9, 0.5, 0.25]):
        color = _blend(bg_color, shadow_color, alpha)
        spread = i * 6
        canvas.create_oval(
            cx - w // 2 - spread, y2 - 2 + i,
            cx + w // 2 + spread, y2 + 4 + i * 3,
            fill=color, outline="",
            tags=tag,
        )


# ── Glass Rounded Rectangle ───────────────────────────────────────────────────
def draw_glass_roundrect(
    canvas: tk.Canvas,
    x1: int, y1: int, x2: int, y2: int,
    radius: int = 12,
    surface_color: str = "#0E1535",
    surface_color2: str = "#141D45",    # lighter end of gradient (top)
    border_color: str = "#1C2860",
    highlight_color: str = "#2A3878",   # top-edge specular highlight
    tag: str = "glass",
    gradient_steps: int = 8,
) -> None:
    """
    Draw a glass-like rounded rectangle using layered fill simulation.

    The gradient (surface_color2 at top → surface_color at bottom) creates the
    impression of downward-fading translucency — as if light from above is
    partially visible through the surface.
    """
    canvas.delete(tag)

    # ── Gradient fill (vertical, top lighter → bottom darker) ────────────────
    grad_h = y2 - y1
    for i in range(gradient_steps):
        t   = i / gradient_steps
        c   = _blend(surface_color2, surface_color, t)
        gy0 = y1 + int(t * grad_h)
        gy1 = y1 + int((i + 1) / gradient_steps * grad_h)
        # clip to rounded corners on first/last strip using full-width rect
        canvas.create_rectangle(
            x1 + radius if gy0 == y1 else x1,
            gy0,
            x2 - radius if gy0 == y1 else x2,
            gy1 if gy1 < y2 else y2,
            fill=c, outline="",
            tags=tag,
        )

    # ── Corner fill (top-left/right and bottom-left/right arcs) ──────────────
    c_top = surface_color2
    c_bot = surface_color
    corners = [
        (x1, y1, x1 + radius*2, y1 + radius*2, 90,  "start", c_top),   # top-left
        (x2 - radius*2, y1, x2, y1 + radius*2, 0,   "start", c_top),   # top-right
        (x1, y2 - radius*2, x1 + radius*2, y2, 180, "start", c_bot),   # bot-left
        (x2 - radius*2, y2 - radius*2, x2, y2, 270, "start", c_bot),   # bot-right
    ]
    for bx1, by1, bx2, by2, start, _, color in corners:
        canvas.create_arc(bx1, by1, bx2, by2, start=start, extent=90,
                          style="pieslice", fill=color, outline="", tags=tag)

    # Fill the main inner rect (covers gradient seam)
    canvas.create_rectangle(
        x1 + radius, y1,
        x2 - radius, y2,
        fill=surface_color, outline="", tags=tag,
    )
    canvas.create_rectangle(
        x1, y1 + radius,
        x2, y2 - radius,
        fill=surface_color, outline="", tags=tag,
    )
    # Re-draw corners solid
    for bx1, by1, bx2, by2, start, _, color in corners:
        canvas.create_arc(bx1, by1, bx2, by2, start=start, extent=90,
                          style="pieslice", fill=color, outline="", tags=tag)

    # ── Border ────────────────────────────────────────────────────────────────
    canvas.create_arc(x1, y1, x1+radius*2, y1+radius*2,
                      start=90, extent=90, style="arc", outline=border_color, width=1, tags=tag)
    canvas.create_arc(x2-radius*2, y1, x2, y1+radius*2,
                      start=0, extent=90, style="arc", outline=border_color, width=1, tags=tag)
    canvas.create_arc(x1, y2-radius*2, x1+radius*2, y2,
                      start=180, extent=90, style="arc", outline=border_color, width=1, tags=tag)
    canvas.create_arc(x2-radius*2, y2-radius*2, x2, y2,
                      start=270, extent=90, style="arc", outline=border_color, width=1, tags=tag)
    canvas.create_line(x1+radius, y1, x2-radius, y1, fill=border_color, width=1, tags=tag)
    canvas.create_line(x1+radius, y2, x2-radius, y2, fill=border_color, width=1, tags=tag)
    canvas.create_line(x1, y1+radius, x1, y2-radius, fill=border_color, width=1, tags=tag)
    canvas.create_line(x2, y1+radius, x2, y2-radius, fill=border_color, width=1, tags=tag)

    # ── Top specular highlight (top-left arc) ─────────────────────────────────
    if highlight_color:
        canvas.create_line(
            x1 + radius, y1 + 1,
            x2 - radius, y1 + 1,
            fill=highlight_color, width=1, tags=tag,
        )
        canvas.create_arc(
            x1 + 1, y1 + 1, x1 + radius * 2 - 1, y1 + radius * 2 - 1,
            start=90, extent=90, style="arc",
            outline=highlight_color, width=1, tags=tag,
        )


# ── Neumorphic Surface ────────────────────────────────────────────────────────
def draw_neu_circle(
    canvas: tk.Canvas,
    cx: int, cy: int, r: int,
    base_color: str = "#0F1535",
    light_shadow: str = "#1E2654",   # top-left lighter shadow
    dark_shadow: str  = "#020408",   # bottom-right darker shadow
    highlight: str    = "#2A3878",   # inner specular arc
    border_color: str = "#1C2860",
    state: str = "normal",           # normal / hover / pressed / active
    accent_color: str = "#38BDF8",
    tag: str = "neu",
) -> None:
    """
    Draw a neumorphic circle button.

    normal:  raised surface — light shadow top-left, dark shadow bottom-right
    hover:   same but brighter surface + accent border
    pressed: inverted — dark shadow top-left (inset illusion)
    active:  accent fill + glow
    """
    canvas.delete(tag)

    if state == "pressed":
        # Inset illusion: swap shadow directions
        _draw_inset_circle(canvas, cx, cy, r, base_color, dark_shadow, light_shadow,
                           border_color, tag)
    elif state == "active":
        _draw_active_circle(canvas, cx, cy, r, accent_color, tag)
    elif state == "hover":
        _draw_raised_circle(canvas, cx, cy, r,
                            _blend(base_color, light_shadow, 0.3),
                            light_shadow, dark_shadow,
                            accent_color, tag)
        canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                           outline=accent_color, width=1, tags=tag)
    else:
        _draw_raised_circle(canvas, cx, cy, r, base_color, light_shadow, dark_shadow,
                            highlight, tag)
        canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                           outline=border_color, width=1, tags=tag)


def _draw_raised_circle(canvas, cx, cy, r, bg, light, dark, hl, tag):
    # Outer dark shadow (bottom-right)
    canvas.create_oval(cx-r+3, cy-r+3, cx+r+3, cy+r+3,
                       fill=dark, outline="", tags=tag)
    # Outer light shadow (top-left)
    canvas.create_oval(cx-r-3, cy-r-3, cx+r-3, cy+r-3,
                       fill=light, outline="", tags=tag)
    # Main surface
    canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                       fill=bg, outline="", tags=tag)
    # Inner specular arc (top-left)
    canvas.create_arc(cx-r+3, cy-r+3, cx+r-3, cy+r-3,
                      start=45, extent=180,
                      style="arc", outline=hl, width=1, tags=tag)


def _draw_inset_circle(canvas, cx, cy, r, bg, top_dark, bot_light, border, tag):
    # No outer shadow for inset
    # Main surface (slightly darker)
    canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                       fill=_blend(bg, "#000000", 0.2), outline=border, width=1, tags=tag)
    # Inner dark shadow at top-left (inset illusion)
    canvas.create_arc(cx-r+2, cy-r+2, cx+r-2, cy+r-2,
                      start=45, extent=180,
                      style="arc", outline=top_dark, width=2, tags=tag)
    # Inner light at bottom-right
    canvas.create_arc(cx-r+2, cy-r+2, cx+r-2, cy+r-2,
                      start=225, extent=180,
                      style="arc", outline=bot_light, width=1, tags=tag)


def _draw_active_circle(canvas, cx, cy, r, accent, tag):
    # Ambient glow ring (outer)
    glow = _blend(accent, "#000000", 0.7)
    canvas.create_oval(cx-r-4, cy-r-4, cx+r+4, cy+r+4,
                       fill=glow, outline="", tags=tag)
    # Main surface with accent tint
    surface = _blend(accent, "#080B1A", 0.82)
    canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                       fill=surface, outline=accent, width=1, tags=tag)
    # Inner highlight
    canvas.create_arc(cx-r+3, cy-r+3, cx+r-3, cy+r-3,
                      start=45, extent=120,
                      style="arc", outline=_blend(accent, "#FFFFFF", 0.3), width=1, tags=tag)


# ── Ambient Glow ──────────────────────────────────────────────────────────────
def draw_ambient_glow(
    canvas: tk.Canvas,
    cx: int, cy: int,
    rx: int, ry: int,
    glow_color: str = "#38BDF8",
    bg_color: str   = "#080B1A",
    intensity: float = 0.15,
    steps: int = 6,
    tag: str = "glow",
) -> None:
    """Soft radial ambient glow — concentric ovals from glow_color → bg_color."""
    canvas.delete(tag)
    for i in range(steps, 0, -1):
        t     = (steps - i) / steps
        t_sq  = t * t
        color = _blend(bg_color, glow_color, t_sq * intensity)
        scale = i / steps
        canvas.create_oval(
            cx - rx * scale, cy - ry * scale,
            cx + rx * scale, cy + ry * scale,
            fill=color, outline="", tags=tag,
        )
