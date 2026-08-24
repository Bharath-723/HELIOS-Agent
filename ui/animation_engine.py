"""
ui/animation_engine.py — HELIOS Animation Engine
=================================================
30fps loop driving the Full Window Edge Glow.

Edge Glow
  • A slow breathing ambient aura around the extreme window boundary
  • Blends Gold, Yellow, Pink, and Sky Blue colors smoothly
  • Breathes in intensity and color based on active state (idle, thinking, etc.)
  • No racing lights, rotating segments, or flashy RGB rings
"""

from __future__ import annotations
import math
import tkinter as tk
from .theme import C, A, S, W, hex_lerp, gradient_at


class AnimationEngine:
    """Orchestrates breathing window ambient edge glow, background orbs, and avatar pulse."""

    def __init__(self, root: tk.Tk, bg_canvas: tk.Canvas,
                 win_w: int, win_h: int) -> None:
        self.root      = root
        self.cv        = bg_canvas
        self.W         = win_w
        self.H         = win_h

        # ── State ────────────────────────────────────────────────────────────
        self._state    = "idle"
        self._phase    = 0.0
        self._pulse_t  = 0.0
        self._success_timer = 0

        # ── Ambient Background Orbs (Extremely slow breathing auroras) ───────
        self._orbs: list[dict] = [
            {"cx": 110, "cy": 200, "r": 160, "px": 0.0, "py": 0.5, "sp": 0.0006, "c": "#0E1835"},
            {"cx": 310, "cy": 350, "r": 140, "px": 1.5, "py": 1.0, "sp": 0.0008, "c": "#091228"},
            {"cx": 200, "cy": 580, "r": 190, "px": 2.5, "py": 1.8, "sp": 0.0004, "c": "#0F152A"},
        ]
        self._orb_items: list[int] = []

        # ── Thinking Dots ────────────────────────────────────────────────────
        self._think_active = False
        self._think_t      = 0.0
        self._think_dots: list[int] = []
        self._think_cv: tk.Canvas | None = None

        # ── Avatar Pulse ─────────────────────────────────────────────────────
        self._avatar_t   = 0.0
        self._avatar_cb: list  = []

        self._running = False
        self._frame   = 0

    # ═════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═════════════════════════════════════════════════════════════════════════
    def start(self) -> None:
        self._running = True
        self._init_orbs()
        self._loop()

    def stop(self) -> None:
        self._running = False

    def set_state(self, state: str) -> None:
        if state not in ["idle", "thinking", "listening", "success", "error"]:
            state = "idle"
        self._state = state
        if state == "success":
            self._success_timer = 30  # duration of success flash

    def set_thinking(self, active: bool, canvas: tk.Canvas = None, dots: list[int] = None) -> None:
        """Expose thinking state for three-dot breathing indicator."""
        self._think_active = active
        if canvas and dots:
            self._think_cv = canvas
            self._think_dots = dots
        if not active:
            self._think_t = 0.0

    def register_avatar(self, canvas: tk.Canvas, item_id: int) -> None:
        self._avatar_cb.append((canvas, item_id))

    def resize(self, w: int, h: int) -> None:
        self.W = w
        self.H = h

    # ═════════════════════════════════════════════════════════════════════════
    # MAIN LOOP
    # ═════════════════════════════════════════════════════════════════════════
    def _loop(self) -> None:
        if not self._running:
            return
        self._frame += 1

        # Advance state indices
        self._phase   = (self._phase + 0.005) % 1.0
        self._pulse_t += 0.04
        self._avatar_t += 0.02
        if self._success_timer > 0:
            self._success_timer -= 1

        # Redraw layers
        self._draw_breathing_edge_glow()
        self._drift_orbs()

        if self._think_active and self._think_cv and self._think_dots:
            self._animate_thinking_dots()

        self._pulse_avatar()

        self.root.after(A.FRAME_MS, self._loop)

    # ═════════════════════════════════════════════════════════════════════════
    # BREATHING EDGE GLOW
    # ═════════════════════════════════════════════════════════════════════════
    def _draw_breathing_edge_glow(self) -> None:
        """
        Draw continuous warm pale-gold / amber perimeter illumination wave.
        Three concentric layers: 1px warm-white core, pale-gold diffusion, amber outer halo.
        Perimeter identity remains warm gold across states and themes.
        """
        self.cv.delete("border")
        W, H = self.W, self.H

        state = self._state
        if state == "thinking":
            speed = 0.08
            base_opacity = 0.45 + 0.25 * math.sin(self._frame * speed)
            color_mod = None
        elif state == "listening":
            speed = 0.05
            base_opacity = 0.40 + 0.20 * math.sin(self._frame * speed)
            color_mod = "#06B6D4"  # Cyan secondary highlight
        elif state == "success":
            pct = self._success_timer / 30.0
            base_opacity = 0.50 * pct
            color_mod = "#10B981"
        elif state == "error":
            speed = 0.10
            base_opacity = 0.50 + 0.20 * math.sin(self._frame * speed)
            color_mod = "#EF4444"
        else:  # idle
            speed = 0.03
            base_opacity = 0.25 + 0.12 * math.sin(self._frame * speed)
            color_mod = None

        # Continuous Warm Gold palette cycle
        gold_palette = ["#FDE047", "#FACC15", "#F59E0B", "#FEF08A"]
        c_idx = (self._frame // 90) % len(gold_palette)
        n_idx = (c_idx + 1) % len(gold_palette)
        blend_t = (self._frame % 90) / 90.0

        target_color = hex_lerp(gold_palette[c_idx], gold_palette[n_idx], blend_t)
        if color_mod:
            target_color = hex_lerp(target_color, color_mod, 0.40)

        # Draw 3 concentric layers: 1px core + diffusion + halo
        layers = [
            (1.0, "#FEF08A", 1.0),                                       # Layer 0: Core warm white highlight
            (2.0, target_color, base_opacity),                            # Layer 1: Main gold diffusion
            (3.0, hex_lerp(target_color, "#F59E0B", 0.5), base_opacity * 0.5), # Layer 2: Amber outer halo
        ]

        for inset, col, alpha in layers:
            glow_col = hex_lerp(C.BG, col, max(0.05, min(1.0, alpha)))
            self.cv.create_rectangle(
                inset, inset, W - inset, H - inset,
                outline=glow_col, width=1,
                tags="border"
            )

    # ═════════════════════════════════════════════════════════════════════════
    # AMBIENT AURORA
    # ═════════════════════════════════════════════════════════════════════════
    def _init_orbs(self) -> None:
        self._orb_items.clear()
        for orb in self._orbs:
            r  = orb["r"]
            cx = orb["cx"]
            cy = orb["cy"]
            iid = self.cv.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=orb["c"], outline="", tags="orb"
            )
            self._orb_items.append(iid)
        self.cv.tag_raise("border", "orb")

    def _drift_orbs(self) -> None:
        t = self._frame * 0.0004
        bg_aurora = C.BG_S
        self.cv.configure(bg=C.BG)

        for idx, orb in enumerate(self._orbs):
            iid = self._orb_items[idx]
            sp  = orb["sp"]
            dx  = 35 * math.sin(t * sp * 1400 + orb["px"])
            dy  = 25 * math.cos(t * sp * 1100 + orb["py"])
            cx  = orb["cx"] + dx
            cy  = orb["cy"] + dy
            r   = orb["r"]
            
            o_color = hex_lerp(bg_aurora, orb["c"], 0.20)
            self.cv.coords(iid, cx - r, cy - r, cx + r, cy + r)
            self.cv.itemconfig(iid, fill=o_color)

    # ═════════════════════════════════════════════════════════════════════════
    # THREE-DOT BREATHING THINKING ANIMATION
    # ═════════════════════════════════════════════════════════════════════════
    def _animate_thinking_dots(self) -> None:
        """Oscillate three horizontal dots — blue → cyan gradient, smooth breathing."""
        from .theme import C, hex_lerp
        self._think_t += 0.06
        t   = self._think_t
        cv  = self._think_cv
        dots = self._think_dots

        # Gradient colors for three dots: blue → mid → cyan
        dot_colors = [C.BLUE, hex_lerp(C.BLUE, C.CYAN, 0.5), C.CYAN]

        cx_start = 12
        dot_gap  = 10
        dot_r    = 4.0
        base_y   = 14

        for i, iid in enumerate(dots):
            # Staggered phase
            phase = i * 0.55
            # Smooth scale oscillation: 0.55 → 1.25
            scale = 0.7 + 0.35 * math.sin(t - phase)
            # Brightness oscillation
            glow  = max(0.25, min(1.0, 0.6 + 0.4 * math.sin(t - phase)))
            # Blend from BG toward dot accent color
            color = hex_lerp(C.BG_S, dot_colors[i], glow)

            cx     = cx_start + i * (dot_r * 2 + dot_gap)
            curr_r = dot_r * scale

            cv.coords(iid,
                      cx - curr_r, base_y - curr_r,
                      cx + curr_r, base_y + curr_r)
            cv.itemconfig(iid, fill=color)


    # ═════════════════════════════════════════════════════════════════════════
    # AVATAR PULSE
    # ═════════════════════════════════════════════════════════════════════════
    def _pulse_avatar(self) -> None:
        t = self._avatar_t
        state = self._state
        
        if state == "idle":
            intensity = 0.15 + 0.08 * math.sin(t * 0.5)
        elif state == "thinking":
            intensity = 0.50 + 0.25 * math.sin(t * 1.5)
        elif state == "listening":
            intensity = 0.60 + 0.20 * math.sin(t * 2.0)
        else:
            intensity = 0.35 + 0.15 * math.sin(t)

        glow_color = hex_lerp(C.BG_S, C.BLUE, intensity)
        for (canvas, item_id) in self._avatar_cb:
            try:
                canvas.itemconfig(item_id, fill=glow_color)
            except Exception:
                pass
