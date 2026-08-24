"""
ui/ambient_background.py — HELIOS v5.0 Atmospheric Ambient Background
=======================================================================
Multi-zone atmospheric canvas with vivid environmental lighting.

Key improvements over v4.x:
  - 3–4x more intense ambient glow zones (previously too dim to see)
  - Central radial vignette (dark center creates depth)
  - Slow breathing animation (8-step, 100ms/step)
  - Horizontal "beam" from top-left (directional light simulation)
  - Light theme: warm blue-gray soft zones
  - Dark theme: deep blue/violet/cyan/rose zones

Architecture:
  - Lives inside background_layer (never root)
  - Uses pack(fill=both, expand=True)
  - NEVER calls lift() or lower()
  - Renders once on init and resize
  - Light animation via after() — idle-rate at 10fps
"""

from __future__ import annotations
import math
import tkinter as tk
from .theme import C, ThemeManager, hex_lerp


class AmbientBackground:
    """
    Background canvas — vivid multi-zone atmospheric glow with slow animation.
    """

    def __init__(self, parent: tk.Widget, width: int, height: int) -> None:
        self.W = width
        self.H = height
        self._phase = 0.0        # breathing animation phase [0, 2π]
        self._after_id = None
        self._animating = False

        self.canvas = tk.Canvas(
            parent,
            width=width, height=height,
            bg=self._floor_color(),
            highlightthickness=0, bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self._render()
        self._start_animation()
        ThemeManager.add_listener(self._on_theme_changed)

    # ── Color helpers ─────────────────────────────────────────────────────────
    def _floor_color(self) -> str:
        return C.AMBIENT_BASE

    def _zone_data(self) -> list:
        """
        Zone definitions tuned for VISIBLE environmental lighting.
        Intensities are 3–4x higher than v4.x.
        Returns list of (cx_frac, cy_frac, rx_frac, ry_frac, color, intensity)
        """
        if ThemeManager.get_mode() == "light":
            return [
                (0.10, 0.18, 0.65, 0.55, "#B8CCF0", 0.38),  # Top-left: cool blue
                (0.90, 0.12, 0.58, 0.45, "#D0C0F8", 0.28),  # Top-right: lavender
                (0.08, 0.82, 0.52, 0.45, "#B0DFF8", 0.25),  # Bot-left: sky
                (0.92, 0.80, 0.50, 0.42, "#F8D0E8", 0.20),  # Bot-right: rose
                (0.50, 0.35, 0.70, 0.50, "#D0DCFF", 0.15),  # Center: subtle blue
            ]
        else:
            return [
                (0.10, 0.18, 0.65, 0.55, "#1E3A8A", 0.60),  # Top-left: deep blue
                (0.88, 0.12, 0.58, 0.45, "#4C1D95", 0.45),  # Top-right: violet
                (0.08, 0.82, 0.52, 0.45, "#0891B2", 0.40),  # Bot-left: cyan
                (0.92, 0.80, 0.50, 0.42, "#831843", 0.30),  # Bot-right: rose
                (0.50, 0.35, 0.70, 0.50, "#0D1224", 0.20),  # Center: dark overlay
            ]

    # ── Render ────────────────────────────────────────────────────────────────
    def _render(self, phase_offset: float = 0.0) -> None:
        """Full re-render: floor + zones + vignette + directional beam."""
        self.canvas.delete("all")
        self._draw_floor()
        self._draw_ambient_zones(phase_offset)
        self._draw_directional_beam()
        self._draw_vignette()

    def _draw_floor(self) -> None:
        """Vertical gradient floor."""
        W, H = self.W, self.H
        steps = 20
        c0 = C.AMBIENT_BASE
        c1 = C.AMBIENT_MID

        r0, g0, b0 = _hex_rgb(c0)
        r1, g1, b1 = _hex_rgb(c1)

        for i in range(steps):
            t  = i / steps
            y0 = int(t * H)
            y1 = int((i + 1) / steps * H)
            r  = int(r0 + (r1 - r0) * t)
            g  = int(g0 + (g1 - g0) * t)
            b  = int(b0 + (b1 - b0) * t)
            self.canvas.create_rectangle(
                0, y0, W, y1,
                fill=f"#{r:02x}{g:02x}{b:02x}", outline="",
                tags="floor",
            )

    def _draw_ambient_zones(self, phase: float = 0.0) -> None:
        """
        Vivid ambient glow zones with breathing pulse.
        Each zone has 12 concentric ovals for smooth falloff.
        """
        W, H = self.W, self.H
        floor_r, floor_g, floor_b = _hex_rgb(C.AMBIENT_BASE)
        steps = 12

        for cx_f, cy_f, rx_f, ry_f, zone_color, intensity in self._zone_data():
            cx = int(cx_f * W)
            cy = int(cy_f * H)
            rx = int(rx_f * W)
            ry = int(ry_f * H)
            zr, zg, zb = _hex_rgb(zone_color)

            # Apply breathing pulse to intensity
            pulse = 1.0 + 0.08 * math.sin(phase + cx_f * 2.0)
            effective = min(1.0, intensity * pulse)

            for i in range(steps, 0, -1):
                t     = (steps - i) / steps     # 0 at outer, 1 at inner
                t_c   = t ** 1.5                  # power curve falloff
                r_    = int(floor_r + (zr - floor_r) * t_c * effective)
                g_    = int(floor_g + (zg - floor_g) * t_c * effective)
                b_    = int(floor_b + (zb - floor_b) * t_c * effective)
                scale = i / steps
                self.canvas.create_oval(
                    cx - rx * scale, cy - ry * scale,
                    cx + rx * scale, cy + ry * scale,
                    fill=f"#{r_:02x}{g_:02x}{b_:02x}",
                    outline="", tags="ambient",
                )

    def _draw_directional_beam(self) -> None:
        """
        Subtle horizontal directional light from top-left.
        Simulates a light source at top-left illuminating the environment.
        """
        if ThemeManager.get_mode() == "dark":
            beam_color = "#0A1E50"
        else:
            beam_color = "#E0EAFF"

        floor_r, floor_g, floor_b = _hex_rgb(C.AMBIENT_BASE)
        br, bg, bb = _hex_rgb(beam_color)
        W, H = self.W, self.H

        steps = 8
        for i in range(steps, 0, -1):
            t = (steps - i) / steps
            t_c = t ** 2
            r_ = int(floor_r + (br - floor_r) * (1 - t_c) * 0.4)
            g_ = int(floor_g + (bg - floor_g) * (1 - t_c) * 0.4)
            b_ = int(floor_b + (bb - floor_b) * (1 - t_c) * 0.4)
            spread = i * W // steps
            self.canvas.create_oval(
                -spread, -H // 2,
                spread * 2, H // 2,
                fill=f"#{r_:02x}{g_:02x}{b_:02x}",
                outline="", tags="beam",
            )

    def _draw_vignette(self) -> None:
        """
        Subtle dark vignette around edges (makes center feel brighter/deeper).
        """
        W, H = self.W, self.H
        if ThemeManager.get_mode() == "dark":
            vig = "#010204"
        else:
            vig = "#D0D8E8"

        steps = 6
        floor_r, floor_g, floor_b = _hex_rgb(C.AMBIENT_BASE)
        vr, vg, vb = _hex_rgb(vig)

        for i in range(steps):
            t     = i / steps
            t_sq  = t * t
            r_    = int(floor_r + (vr - floor_r) * t_sq * 0.5)
            g_    = int(floor_g + (vg - floor_g) * t_sq * 0.5)
            b_    = int(floor_b + (vb - floor_b) * t_sq * 0.5)
            extra = i * max(W, H) // steps
            self.canvas.create_oval(
                -extra, -extra,
                W + extra, H + extra,
                fill=f"#{r_:02x}{g_:02x}{b_:02x}",
                outline="", tags="vignette",
            )

    # ── Animation ─────────────────────────────────────────────────────────────
    def _start_animation(self) -> None:
        self._animating = True
        self._tick()

    def _tick(self) -> None:
        if not self._animating:
            return
        try:
            if not self.canvas.winfo_exists():
                return
        except Exception:
            return

        self._phase = (self._phase + 0.08) % (2 * math.pi)
        self._render(self._phase)
        # Slow tick — 150ms for gentle breathing (not distracting)
        self._after_id = self.canvas.after(150, self._tick)

    def stop_animation(self) -> None:
        self._animating = False
        if self._after_id:
            try:
                self.canvas.after_cancel(self._after_id)
            except Exception:
                pass

    # ── Resize / Theme ────────────────────────────────────────────────────────
    def resize(self, width: int, height: int) -> None:
        self.W = width
        self.H = height
        self.canvas.configure(width=width, height=height)
        self._render(self._phase)

    def _on_theme_changed(self) -> None:
        self.canvas.configure(bg=self._floor_color())
        self._render(self._phase)


def _hex_rgb(color: str) -> tuple[int, int, int]:
    try:
        return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    except Exception:
        return 8, 11, 26
