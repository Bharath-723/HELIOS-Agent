"""
ui/theme.py — HELIOS v4.0 Design Token System & Theme Engine
=============================================================
Premium Cognitive Operating System visual language.

Five-level glass depth system:
  GLASS_1 — Background base (window floor)
  GLASS_2 — Standard panel surface (nav rail, side panels)
  GLASS_3 — Elevated card (message cards, session items)
  GLASS_4 — Modal / dialog surface (settings drawer)
  GLASS_5 — Floating control (command bar, tooltips)

DPI notes:
  Tkinter font sizes are in POINTS — device-independent.
  Do NOT scale font sizes with _DPI_SCALE.
  Use px() only for pixel-based layout dimensions (heights, widths, padx/pady)
  when you intend to honour DPI. Existing hardcoded dimensions remain untouched
  to avoid breaking the layout — use px() in NEW components only.

Color Palette: Deep Navy & Precision Accents
  Primary:   #080B1A (Deep Navy)
  Accent:    #3B82F6 (Precision Blue)
  Secondary: Cyan #06B6D4 / Violet #8B5CF6 / Emerald #10B981
"""

from __future__ import annotations
import sys
import tkinter as tk

# ── DPI Scale Detection ───────────────────────────────────────────────────────
def _detect_dpi_scale() -> float:
    """
    Detect effective layout scale for pixel-based dimensions.

    Returns 1.0 when Tkinter is NOT DPI-aware (virtualized DPI — default).
    Returns actual scale when SetProcessDpiAwareness >= 1 has been called.

    Important: Tkinter without explicit DPI awareness uses system DPI virtualisation
    and already receives logical pixels at 96-DPI equivalence — scale = 1.0.
    """
    if sys.platform != "win32":
        return 1.0
    try:
        import ctypes
        awareness = ctypes.c_int(0)
        try:
            ctypes.windll.shcore.GetProcessDpiAwareness(None, ctypes.byref(awareness))
        except Exception:
            awareness.value = 0

        if awareness.value >= 1:
            hdc = ctypes.windll.user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)   # LOGPIXELSX
            ctypes.windll.user32.ReleaseDC(0, hdc)
            scale = dpi / 96.0
            # Round to nearest 0.25 to avoid sub-pixel jitter
            return max(1.0, min(4.0, round(scale * 4) / 4))
        return 1.0
    except Exception:
        return 1.0


_DPI_SCALE: float = _detect_dpi_scale()


def px(value: int | float) -> int:
    """
    Convert a 100%-DPI design pixel value to a DPI-aware pixel value.
    Use for NEW layout pixel dimensions in components written after v4.0.
    Do NOT apply to existing hardcoded dimensions unless refactoring the full
    component layout — changing just one value will break proportions.
    """
    return max(1, round(value * _DPI_SCALE))


# ── Color Presets ─────────────────────────────────────────────────────────────

_DARK_THEME = {
    # ── Core Background System ───────────────────────────────────────────────
    "BG":          "#080B1A",   # Deep Navy — window base (GL1)
    "BG_S":        "#0C1026",   # Surface — scrollable content areas
    "BG_C":        "#111635",   # Card background
    "BG_C2":       "#171D45",   # Elevated card
    "BG_INPUT":    "#0A0E28",   # Input area
    "BG_HOVER":    "#1F2654",   # Hover state surface
    "BG_ACTIVE":   "#252E66",   # Selected / active surface
    "BG_OVERLAY":  "#040612",   # Modal dim overlay

    # ── Five-Level Glass Depth System ────────────────────────────────────────
    # Simulates VisionOS-like spatial layering over the deep navy background.
    # Each level appears progressively lighter / more elevated.
    "GLASS_1":     "#080B1A",   # L1 — Window background (same as BG)
    "GLASS_2":     "#0B1128",   # L2 — Navigation rail, side panels
    "GLASS_3":     "#111840",   # L3 — Message cards, session cards (premium surface)
    "GLASS_4":     "#18204C",   # L4 — Settings drawer, modal surfaces
    "GLASS_5":     "#1D274F",   # L5 — Command bar, tooltips (highest elevation)

    # Glass borders — inner stroke for each depth level
    "GLASS_BD_1":  "#0E1435",
    "GLASS_BD_2":  "#162054",
    "GLASS_BD_3":  "#1D2964",
    "GLASS_BD_4":  "#273678",
    "GLASS_BD_5":  "#324499",

    # Glass inner highlight — simulates top-edge light on a glass surface
    "GLASS_HL":    "#1E2860",

    # ── Shadow Simulation ────────────────────────────────────────────────────
    # Used as background color for offset shadow-simulating frames.
    "SHADOW_SM":   "#030509",
    "SHADOW_MD":   "#020407",
    "SHADOW_LG":   "#010204",

    # ── Glow / Halo Colors ───────────────────────────────────────────────────
    # Dim, desaturated accent colors used for canvas glow rings.
    "GLOW_ACCENT": "#0F2050",   # Blue halo
    "GLOW_OK":     "#053325",   # Emerald halo
    "GLOW_ERR":    "#4A0F0F",   # Red halo
    "GLOW_WARN":   "#3A2200",   # Amber halo

    # ── Edge / Perimeter Illumination ────────────────────────────────────────
    # Continuous soft perimeter light wave — non-rotating, state-driven.
    "EDGE_IDLE":    "#FEF08A",  # Soft gold — preserved HELIOS identity
    "EDGE_THINK":   "#3B82F6",  # Blue — processing
    "EDGE_LISTEN":  "#06B6D4",  # Cyan — listening
    "EDGE_SUCCESS": "#10B981",  # Emerald — success flash
    "EDGE_ERROR":   "#EF4444",  # Red — error flash

    # ── Border System ────────────────────────────────────────────────────────
    "BORDER":      "#1E254A",
    "BORDER_2":    "#293366",
    "BORDER_3":    "#3B4A94",

    # ── Accent: Blue ─────────────────────────────────────────────────────────
    "BLUE":        "#3B82F6",
    "BLUE_D":      "#1D4ED8",
    "BLUE_L":      "#60A5FA",
    "BLUE_DIM":    "#16224F",

    # ── Accent: Cyan ─────────────────────────────────────────────────────────
    "CYAN":        "#06B6D4",
    "CYAN_D":      "#0891B2",
    "CYAN_L":      "#22D3EE",

    # ── Accent: Violet ───────────────────────────────────────────────────────
    "VIOLET":      "#8B5CF6",
    "VIOLET_L":    "#C084FC",

    # ── Semantic Status ──────────────────────────────────────────────────────
    "OK":          "#10B981",
    "OK_D":        "#064E3B",
    "OK_L":        "#34D399",

    "WARN":        "#F59E0B",
    "WARN_D":      "#78350F",
    "WARN_L":      "#FBBF24",

    "ERR":         "#EF4444",
    "ERR_D":       "#991B1B",
    "ERR_L":       "#F87171",

    # ── Typography ───────────────────────────────────────────────────────────
    "FG_1":        "#F1F5F9",   # Slate-100 — primary text
    "FG_2":        "#94A3B8",   # Slate-400 — secondary
    "FG_3":        "#475569",   # Slate-600 — muted
    "FG_4":        "#334155",   # Slate-700 — very muted / tags
    "FG_USER":     "#FFFFFF",
    "FG_HELIOS":   "#E8EDF5",

    # ── Navigation Rail ──────────────────────────────────────────────────────
    "NAV_BG":      "#050712",   # Deepest layer — darkest navy
    "NAV_HOVER":   "#0A0F27",
    "NAV_ACTIVE":  "#121A3A",
    "NAV_ICON":    "#374B6A",   # Calm default icon color
    "NAV_ICON_A":  "#3B82F6",   # Active icon: blue

    # ── Status Bar ───────────────────────────────────────────────────────────
    "STATUS_BG":   "#04060F",
    "STATUS_FG":   "#374B6A",

    # ── User Message Bubble ──────────────────────────────────────────────────
    "USER_BG":     "#14285C",   # Deep blue — glass-like user bubble
    "USER_BG2":    "#1B3270",
    "USER_BORDER": "#2B4FA0",   # Subtle blue border

    # ── Assistant Response Card ──────────────────────────────────────────────
    "CARD_BG":     "#0F1430",
    "CARD_BD":     "#1A2255",
    "CARD_ACCENT": "#1D2A66",

    # ── Thinking Indicator ───────────────────────────────────────────────────
    "THINK_BAR":   "#3B82F6",
    "THINK_BAR_2": "#06B6D4",
    "THINK_BG":    "#0C1026",

    # ── Chips / Tags / Badges ────────────────────────────────────────────────
    "CHIP_BG":     "#111B3A",
    "CHIP_BD":     "#1E2A5E",
    "CHIP_FG":     "#60A5FA",

    # ── Error Cards ──────────────────────────────────────────────────────────
    "ERR_CARD_BG": "#190808",
    "ERR_CARD_BD": "#481010",
    "ERR_CARD_FG": "#F87171",
    "ERR_CARD_HL": "#5A1414",   # Error card accent line

    # ── 9-State UI Machine Colors ─────────────────────────────────────────────
    # Used by ThinkingIndicator dot colors and StatusBar state indicators.
    "STATE_IDLE":      "#475569",   # Slate-600 — calm/neutral
    "STATE_THINKING":  "#3B82F6",   # Blue — LLM processing
    "STATE_WORKING":   "#06B6D4",   # Cyan — desktop/action execution
    "STATE_VERIFYING": "#F59E0B",   # Amber — screen verification
    "STATE_WAITING":   "#06B6D4",   # Cyan — waiting for user
    "STATE_SUCCESS":   "#10B981",   # Emerald — completed
    "STATE_WARNING":   "#F59E0B",   # Amber — needs attention
    "STATE_ERROR":     "#EF4444",   # Red — failure
    "STATE_STOPPED":   "#475569",   # Slate — stopped

    # ── Neumorphic Surfaces ───────────────────────────────────────────────────
    # Simulated depth for buttons/icons in nav rail and input controls.
    # NEU_RAISED: default button surface (slightly lighter than BG_C)
    # NEU_PRESSED: pressed state (slightly darker — inset illusion)
    "NEU_RAISED":  "#131838",   # Raised button surface
    "NEU_PRESSED": "#0A0E22",   # Pressed/inset surface
    "NEU_BORDER":  "#1A2040",   # Subtle border for neumorphic elements
    "NEU_INSET":   "#060911",   # Deeply inset surface
    "NEU_LIGHT":   "#1E2654",   # Light shadow edge (top-left)
    "NEU_DARK":    "#03040D",   # Dark shadow edge (bottom-right)

    # ── Gold / Amber Accent ────────────────────────────────────────────────────
    "GOLD":        "#F59E0B",
    "GOLD_L":      "#FCD34D",
    "GOLD_D":      "#92400E",

    # ── 5-Level Semantic Depth System ─────────────────────────────────────────
    # Z-axis elevation: DEPTH_0 = floor, DEPTH_4 = most elevated
    "DEPTH_0": "#060914",   # Floor (window root background)
    "DEPTH_1": "#0A0F20",   # Base panels (nav rail, header, input)
    "DEPTH_2": "#0E1535",   # Cards (messages, session items)
    "DEPTH_3": "#121C44",   # Elevated cards (settings drawer)
    "DEPTH_4": "#172150",   # Floating controls (command bar, tooltips)

    # Depth border colors (inner stroke at each elevation)
    "DEPTH_BD_0": "#0E1430",
    "DEPTH_BD_1": "#152048",
    "DEPTH_BD_2": "#1C2860",
    "DEPTH_BD_3": "#233278",
    "DEPTH_BD_4": "#2E4299",

    # ── Material Glass Surface System ──────────────────────────────────────────
    "MATERIAL_GLASS":        "#0E1535",
    "MATERIAL_GLASS_ACTIVE": "#14204A",
    "MATERIAL_GLASS_HOVER":  "#111A3E",
    "MATERIAL_GLASS_PRESSED":"#0A0F28",
    "MATERIAL_GLASS_BD":     "#1C2860",
    "MATERIAL_GLASS_HL":     "#202E6A",
    "MATERIAL_GLASS_SHADOW": "#02030A",

    # ── Ambient Environment Lighting ───────────────────────────────────────────
    # Rich environmental lighting falloffs for background atmosphere.
    "AMBIENT_BASE":   "#080B18",   # Deep space floor color
    "AMBIENT_BLUE":   "#1E3A8A",   # Deep blue glow zone
    "AMBIENT_VIOLET": "#4C1D95",   # Deep violet glow zone
    "AMBIENT_CYAN":   "#0891B2",   # Deep cyan glow zone
    "AMBIENT_PINK":   "#831843",   # Deep rose glow zone
    "AMBIENT_MID":    "#0D1224",   # Central navy floor
}


_LIGHT_THEME = {
    # ── Core Background System ───────────────────────────────────────────────
    "BG":          "#F8FAFC",
    "BG_S":        "#FFFFFF",
    "BG_C":        "#F1F5F9",
    "BG_C2":       "#E2E8F0",
    "BG_INPUT":    "#FFFFFF",
    "BG_HOVER":    "#E8EEF8",
    "BG_ACTIVE":   "#D4DDF0",
    "BG_OVERLAY":  "#0F172A",

    # ── Five-Level Glass Depth System ────────────────────────────────────────
    "GLASS_1":     "#F8FAFC",
    "GLASS_2":     "#FFFFFF",
    "GLASS_3":     "#F2F6FC",
    "GLASS_4":     "#EBF0FA",
    "GLASS_5":     "#E3EAF8",

    "GLASS_BD_1":  "#E2E8F0",
    "GLASS_BD_2":  "#C8D5E8",
    "GLASS_BD_3":  "#B5C4DC",
    "GLASS_BD_4":  "#98AFC8",
    "GLASS_BD_5":  "#7894BB",

    "GLASS_HL":    "#FFFFFF",

    # ── Shadow Simulation ────────────────────────────────────────────────────
    "SHADOW_SM":   "#E8EEF8",
    "SHADOW_MD":   "#D8E2F4",
    "SHADOW_LG":   "#C4D0EC",

    # ── Glow / Halo ──────────────────────────────────────────────────────────
    "GLOW_ACCENT": "#DBEAFE",
    "GLOW_OK":     "#D1FAE5",
    "GLOW_ERR":    "#FEE2E2",
    "GLOW_WARN":   "#FEF3C7",

    # ── Edge / Perimeter Illumination ────────────────────────────────────────
    # Warm pale-yellow / gold continuous identity across both themes
    "EDGE_IDLE":    "#FACC15",   # Warm Gold
    "EDGE_THINK":   "#EAB308",   # Gold pulse
    "EDGE_LISTEN":  "#F59E0B",   # Amber
    "EDGE_SUCCESS": "#10B981",   # Emerald flash
    "EDGE_ERROR":   "#EF4444",   # Red error flash

    # ── Borders ──────────────────────────────────────────────────────────────
    "BORDER":      "#E2E8F0",
    "BORDER_2":    "#CBD5E1",
    "BORDER_3":    "#94A3B8",

    # ── Accent: Blue ─────────────────────────────────────────────────────────
    "BLUE":        "#2563EB",
    "BLUE_D":      "#1D4ED8",
    "BLUE_L":      "#3B82F6",
    "BLUE_DIM":    "#DBEAFE",

    # ── Accent: Cyan ─────────────────────────────────────────────────────────
    "CYAN":        "#0891B2",
    "CYAN_D":      "#0E7490",
    "CYAN_L":      "#06B6D4",

    # ── Accent: Violet ───────────────────────────────────────────────────────
    "VIOLET":      "#7C3AED",
    "VIOLET_L":    "#A78BFA",

    # ── Semantic Status ──────────────────────────────────────────────────────
    "OK":          "#059669",
    "OK_D":        "#D1FAE5",
    "OK_L":        "#10B981",

    "WARN":        "#D97706",
    "WARN_D":      "#FEF3C7",
    "WARN_L":      "#F59E0B",

    "ERR":         "#DC2626",
    "ERR_D":       "#FEE2E2",
    "ERR_L":       "#EF4444",

    # ── Typography ───────────────────────────────────────────────────────────
    "FG_1":        "#0F172A",
    "FG_2":        "#334155",
    "FG_3":        "#64748B",
    "FG_4":        "#94A3B8",
    "FG_USER":     "#FFFFFF",
    "FG_HELIOS":   "#1E293B",

    # ── Navigation ───────────────────────────────────────────────────────────
    "NAV_BG":      "#F0F4FC",
    "NAV_HOVER":   "#E2E8F4",
    "NAV_ACTIVE":  "#D4DCEE",
    "NAV_ICON":    "#64748B",
    "NAV_ICON_A":  "#2563EB",

    # ── Status Bar ───────────────────────────────────────────────────────────
    "STATUS_BG":   "#E8EEF8",
    "STATUS_FG":   "#475569",

    # ── User Message Bubble ──────────────────────────────────────────────────
    "USER_BG":     "#2563EB",
    "USER_BG2":    "#1D4ED8",
    "USER_BORDER": "#3B82F6",

    # ── Assistant Response Card ──────────────────────────────────────────────
    "CARD_BG":     "#FFFFFF",
    "CARD_BD":     "#E0E8F8",
    "CARD_ACCENT": "#DBEAFE",

    # ── Thinking Indicator ───────────────────────────────────────────────────
    "THINK_BAR":   "#2563EB",
    "THINK_BAR_2": "#3B82F6",
    "THINK_BG":    "#F8FAFC",

    # ── Chips / Tags / Badges ────────────────────────────────────────────────
    "CHIP_BG":     "#DBEAFE",
    "CHIP_BD":     "#BFDBFE",
    "CHIP_FG":     "#1D4ED8",

    # ── Error Cards ──────────────────────────────────────────────────────────
    "ERR_CARD_BG": "#FFF5F5",
    "ERR_CARD_BD": "#FECACA",
    "ERR_CARD_FG": "#DC2626",
    "ERR_CARD_HL": "#FCA5A5",

    # ── 9-State UI Machine Colors ─────────────────────────────────────────────
    "STATE_IDLE":      "#64748B",
    "STATE_THINKING":  "#2563EB",
    "STATE_WORKING":   "#0891B2",
    "STATE_VERIFYING": "#D97706",
    "STATE_WAITING":   "#0891B2",
    "STATE_SUCCESS":   "#059669",
    "STATE_WARNING":   "#D97706",
    "STATE_ERROR":     "#DC2626",
    "STATE_STOPPED":   "#64748B",

    # ── Neumorphic Surfaces ───────────────────────────────────────────────────
    "NEU_RAISED":  "#FFFFFF",
    "NEU_PRESSED": "#E8EEF8",
    "NEU_BORDER":  "#CBD5E1",
    "NEU_INSET":   "#E0E8F0",
    "NEU_LIGHT":   "#FFFFFF",
    "NEU_DARK":    "#C0CEDF",

    # ── Gold / Amber Accent ─────────────────────────────────────────────────
    "GOLD":        "#D97706",
    "GOLD_L":      "#F59E0B",
    "GOLD_D":      "#FEF3C7",

    # ── 5-Level Semantic Depth System ──────────────────────────────────────
    "DEPTH_0": "#F8FAFC",   # Floor
    "DEPTH_1": "#FFFFFF",   # Base panels
    "DEPTH_2": "#F1F5F9",   # Cards
    "DEPTH_3": "#E8EEF8",   # Elevated cards
    "DEPTH_4": "#E0E8F4",   # Floating controls

    # Depth border colors
    "DEPTH_BD_0": "#E2E8F0",
    "DEPTH_BD_1": "#D0D9E8",
    "DEPTH_BD_2": "#C0CEDF",
    "DEPTH_BD_3": "#AABCD2",
    "DEPTH_BD_4": "#90A9C5",

    # ── Material Glass Surface System ───────────────────────────────────────
    "MATERIAL_GLASS":        "#F1F5F9",
    "MATERIAL_GLASS_ACTIVE": "#E3EEF8",
    "MATERIAL_GLASS_HOVER":  "#EAF2F8",
    "MATERIAL_GLASS_PRESSED":"#D4E0F0",
    "MATERIAL_GLASS_BD":     "#C0CEDF",
    "MATERIAL_GLASS_HL":     "#FFFFFF",
    "MATERIAL_GLASS_SHADOW": "#C0CEDF",

    # ── Ambient Environment Lighting ────────────────────────────────────────
    "AMBIENT_BASE":   "#F8FAFC",
    "AMBIENT_BLUE":   "#EBF4FF",
    "AMBIENT_VIOLET": "#F3EEFF",
    "AMBIENT_CYAN":   "#E8F9FF",
    "AMBIENT_PINK":   "#FFF0F6",
    "AMBIENT_MID":    "#F5F8FF",
}


# ── Theme Manager ─────────────────────────────────────────────────────────────
class ThemeManager:
    """Manages active theme preset and handles animated transitions."""

    _mode: str = "dark"
    _resolved_theme = dict(_DARK_THEME)
    _listeners: list = []
    _reduced_motion: bool = False

    @classmethod
    def set_mode(cls, mode: str, root: tk.Tk | None = None) -> None:
        """Switch theme. Animates over ~60ms if root is provided and not reduced-motion."""
        cls._mode = mode.lower()

        # Resolve target palette
        if cls._mode == "light":
            target_theme = _LIGHT_THEME
        elif cls._mode == "dark":
            target_theme = _DARK_THEME
        else:  # system
            target_theme = _LIGHT_THEME if cls.get_windows_light_theme() else _DARK_THEME

        if not root or cls._reduced_motion:
            cls._resolved_theme = dict(target_theme)
            cls.notify()
            return

        # Smooth animated transition — 4 steps × 15ms ≈ 60ms
        old_theme = dict(cls._resolved_theme)
        steps = 4

        def _step(i: int = 1) -> None:
            if i > steps:
                cls._resolved_theme = dict(target_theme)
                cls.notify()
                return
            t = i / steps
            for k in target_theme.keys():
                old_val = old_theme.get(k, target_theme[k])
                cls._resolved_theme[k] = hex_lerp(old_val, target_theme[k], t)
            cls.notify()
            root.after(15, lambda: _step(i + 1))

        _step(1)

    @classmethod
    def set_reduced_motion(cls, enabled: bool) -> None:
        """Enable/disable reduced-motion mode for accessibility."""
        cls._reduced_motion = enabled

    @classmethod
    def get_reduced_motion(cls) -> bool:
        return cls._reduced_motion

    @classmethod
    def get_mode(cls) -> str:
        return cls._mode

    @classmethod
    def resolve(cls) -> None:
        """Instantly snap to current theme without animation."""
        if cls._mode == "light":
            cls._resolved_theme = dict(_LIGHT_THEME)
        elif cls._mode == "dark":
            cls._resolved_theme = dict(_DARK_THEME)
        else:
            cls._resolved_theme = dict(
                _LIGHT_THEME if cls.get_windows_light_theme() else _DARK_THEME
            )

    @classmethod
    def get_windows_light_theme(cls) -> bool:
        if sys.platform != "win32":
            return False
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return val == 1
        except Exception:
            return False

    @classmethod
    def get_color(cls, key: str) -> str:
        return cls._resolved_theme.get(key, "#ffffff")

    @classmethod
    def add_listener(cls, cb) -> None:
        if cb not in cls._listeners:
            cls._listeners.append(cb)

    @classmethod
    def remove_listener(cls, cb) -> None:
        try:
            cls._listeners.remove(cb)
        except ValueError:
            pass

    @classmethod
    def notify(cls) -> None:
        for cb in list(cls._listeners):
            try:
                cb()
            except Exception:
                pass


# ── Color Proxy Wrapper ───────────────────────────────────────────────────────
class ColorProxy:
    """Dynamic color accessor — reads from the resolved theme at call time."""

    def __getattr__(self, name: str) -> str:
        return ThemeManager.get_color(name)


C = ColorProxy()


# ── Font System ───────────────────────────────────────────────────────────────
class F:
    """
    Font tokens — all sizes are in POINTS (device-independent).

    Tkinter renders point sizes at the correct physical density regardless of
    DPI. Do NOT multiply these by _DPI_SCALE.
    """
    _PRIMARY  = "Segoe UI Variable Display"   # Windows 11 variable font
    _MONO     = "Cascadia Code"               # Monospace / code
    _FALLBACK = "Segoe UI"                    # Universal Windows fallback
    _ICON     = "Segoe Fluent Icons"          # Windows 11 icon font
    _ICON_ALT = "Segoe MDL2 Assets"           # Windows 10 icon font
    _SYMBOL   = "Segoe UI Symbol"             # General Unicode symbols

    # Point sizes (device-independent — do not scale)
    XS   = 11   # Caption, metadata, timestamps (min readable size)
    SM   = 12   # Small UI text, status bar
    MD   = 13   # Body text (default)
    LG   = 15   # Emphasis, section labels
    XL   = 18   # Section headers / title
    XXL  = 24   # Display title
    XXXL = 30   # Hero greeting

    @classmethod
    def ui(cls, size: int = 10, weight: str = "normal") -> tuple:
        return (cls._PRIMARY, size, weight)

    @classmethod
    def sans(cls, size: int = 10, weight: str = "normal") -> tuple:
        return (cls._FALLBACK, size, weight)

    @classmethod
    def mono(cls, size: int = 9, weight: str = "normal") -> tuple:
        return (cls._MONO, size, weight)


# ── Spacing Tokens ────────────────────────────────────────────────────────────
class S:
    """Layout spacing and component dimension tokens (logical pixels)."""

    XS  = 4
    SM  = 8
    MD  = 12
    LG  = 16
    XL  = 24
    XXL = 32

    # Core component dimensions
    NAV_W       = 56     # Navigation rail width (↑ from 52 for breathing room)
    HEADER_H    = 60     # Header bar height
    INPUT_H     = 84     # Input panel total height (preserved)
    STATUS_H    = 26     # Status bar height
    BORDER_W    = 2      # Window border weight
    CARD_RADIUS = 10     # Card corner radius for canvas drawing
    MSG_PAD     = 14     # Message card horizontal padding
    MSG_GAP     = 8      # Gap between message cards

    # Command bar
    CMD_H       = 52     # Command bar capsule height
    CMD_ICON    = 32     # Icon button canvas size
    CMD_RADIUS  = 22     # Capsule radius for canvas drawing

    # Thinking indicator
    THINK_DOT_R  = 4
    THINK_DOT_GAP = 10


# ── Window Configuration ──────────────────────────────────────────────────────
class W:
    """Window geometry defaults — saves/restores from data/window_settings.json."""
    WIDTH  = 460     # Default width (slightly wider for spatial breathing)
    HEIGHT = 740     # Default height
    MIN_W  = 440     # Minimum (remains usable on 1366×768 screens)
    MIN_H  = 680     # Minimum height
    BORDER = 2       # Window border width
    ALPHA  = 0.98    # Window alpha (slight translucency when behind glass)


# ── Animation Tokens ──────────────────────────────────────────────────────────
class A:
    """Animation timing, easing, and edge-glow palette."""

    FPS       = 60          # Target animation framerate
    FRAME_MS  = 16          # ms per frame at 60fps
    IDLE_FPS  = 10          # Reduced FPS during idle (saves CPU)
    IDLE_MS   = 100         # ms per frame at idle FPS

    FADE_IN    = 250        # Fade-in duration in ms
    FADE_STEPS = 8          # Steps for fade animation

    # Soft perimeter light wave — preserved HELIOS identity colors
    # Non-rotating: wave amplitude/brightness modulated by sin(), not angle
    GLOW_COLORS = [
        "#FEF08A",  # Soft gold (primary identity)
        "#FBCFE8",  # Soft pink
        "#BAE6FD",  # Sky blue
        "#FCD34D",  # Warm amber
    ]

    # Easing helpers (pre-computed t-steps for 6 animation frames)
    EASE_OUT   = [0.0, 0.30, 0.60, 0.80, 0.93, 1.0]   # Decelerate
    EASE_IN    = [0.0, 0.07, 0.20, 0.40, 0.70, 1.0]   # Accelerate
    EASE_INOUT = [0.0, 0.15, 0.40, 0.60, 0.85, 1.0]   # Symmetric


# ── Gradient / Color Utilities ────────────────────────────────────────────────
def hex_lerp(c1: str, c2: str, t: float) -> str:
    """Linear interpolation between two hex colors."""
    t = max(0.0, min(1.0, t))
    try:
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    except (ValueError, IndexError):
        return c2
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def gradient_at(stops: list, t: float) -> str:
    """Evaluate a multi-stop color gradient at position t ∈ [0, 1]."""
    if not stops:
        return "#ffffff"
    n = len(stops) - 1
    if n <= 0:
        return stops[0]
    t = max(0.0, min(1.0, t))
    seg = min(int(t * n), n - 1)
    local_t = (t * n) - seg
    return hex_lerp(stops[seg], stops[seg + 1], local_t)


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out: fast start, smooth deceleration."""
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out: smooth start and end."""
    t = max(0.0, min(1.0, t))
    return 3.0 * t**2 - 2.0 * t**3


# ── Reusable Scrollable Wrapper ───────────────────────────────────────────────
class ScrollableContainer:
    """Wraps a parent widget in a scrollable canvas + vertical scrollbar."""

    def __init__(self, parent: tk.Widget, bg: str) -> None:
        self.canvas = tk.Canvas(parent, bg=bg, highlightthickness=0, bd=0)
        self.vsb    = tk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")

        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win  = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>",  self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.bind_scroll(self.inner)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_inner_configure(self, e: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, e: tk.Event) -> None:
        self.canvas.itemconfig(self._win, width=e.width)

    def _on_mousewheel(self, e: tk.Event) -> None:
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def bind_scroll(self, w: tk.Widget) -> None:
        w.bind("<MouseWheel>", self._on_mousewheel)
        for child in w.winfo_children():
            self.bind_scroll(child)
