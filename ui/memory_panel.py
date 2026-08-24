"""
ui/memory_panel.py — HELIOS Memory Hierarchy Visualization
===========================================================
Visualizes the four-layer memory system.
"""

from __future__ import annotations
import tkinter as tk
from datetime import datetime
from .theme import C, F, S, ThemeManager
from .icon_manager import I

_MEMORY_LAYERS = [
    {
        "key":       "working",
        "level":     "L1",
        "name":      "Working Memory",
        "icon":      I.L1,
        "desc":      "Active context for the current conversation turn.",
        "color_key": "BLUE",
        "max_items": 32,
    },
    {
        "key":       "session",
        "level":     "L2",
        "name":      "Session Memory",
        "icon":      I.L2,
        "desc":      "Accumulated knowledge across this session.",
        "color_key": "CYAN",
        "max_items": 256,
    },
    {
        "key":       "persistent",
        "level":     "L3",
        "name":      "Persistent Memory",
        "icon":      I.L3,
        "desc":      "Cross-session learned preferences and knowledge.",
        "color_key": "VIOLET_L",
        "max_items": 4096,
    },
    {
        "key":       "knowledge",
        "level":     "L4",
        "name":      "Knowledge Memory",
        "icon":      I.L4,
        "desc":      "Static knowledge base and vector document store.",
        "color_key": "OK",
        "max_items": 100000,
    },
]


class MemoryPanel:
    """Memory hierarchy visualization panel."""

    def __init__(self, parent: tk.Widget) -> None:
        self._parent = parent
        self.frame   = tk.Frame(parent, bg=C.BG_S)
        self._bars:  dict[str, tk.Frame] = {}
        self._stats: dict[str, tk.Label] = {}
        self._counts: dict[str, int] = {}
        
        self._build()
        ThemeManager.add_listener(self._on_theme_changed)

    # ─────────────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # Header
        self.hdr = tk.Frame(self.frame, bg=C.BG_C, height=48)
        self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)
        
        self.lbl_title = tk.Label(self.hdr, text="  ◉ Memory Hierarchy",
                                  font=(F._PRIMARY, F.LG, "bold"),
                                  bg=C.BG_C, fg=C.FG_1)
        self.lbl_title.pack(side="left", pady=14)

        # Scrollable area
        self.cv  = tk.Canvas(self.frame, bg=C.BG_S, highlightthickness=0)
        self.vsb = tk.Scrollbar(self.frame, orient="vertical", command=self.cv.yview)
        self.cv.configure(yscrollcommand=self.vsb.set)
        self.cv.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")

        self._inner = tk.Frame(self.cv, bg=C.BG_S)
        self.wid = self.cv.create_window((0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>", lambda e: self.cv.configure(scrollregion=self.cv.bbox("all")))
        self.cv.bind("<Configure>", lambda e: self.cv.itemconfig(self.wid, width=e.width))
        self.cv.bind("<MouseWheel>", lambda e: self.cv.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self._inner.bind("<MouseWheel>", lambda e: self.cv.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Intro
        self.lbl_intro = tk.Label(self._inner,
                                  text="  HELIOS manages a four-layer memory architecture.\n  Each layer has different scope, capacity and persistence.",
                                  font=(F._FALLBACK, F.SM),
                                  bg=C.BG_S, fg=C.FG_3,
                                  justify="left", pady=8)
        self.lbl_intro.pack(fill="x")

        self.sep = tk.Frame(self._inner, bg=C.BORDER, height=1)
        self.sep.pack(fill="x", padx=8, pady=(0, 8))

        self._render_layers()

    def _render_layers(self) -> None:
        for w in self._inner.winfo_children():
            if w not in (self.lbl_intro, self.sep):
                w.destroy()

        for layer in _MEMORY_LAYERS:
            self._layer_card(self._inner, layer)

    def _layer_card(self, parent: tk.Widget, layer: dict) -> None:
        key = layer["key"]
        color = getattr(C, layer["color_key"])

        card = tk.Frame(parent, bg=C.BG_C, highlightthickness=1, highlightbackground=C.BORDER)
        card.pack(fill="x", padx=10, pady=5)

        accent = tk.Frame(card, bg=color, width=4)
        accent.pack(side="left", fill="y")

        body = tk.Frame(card, bg=C.BG_C)
        body.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        # Top row
        top = tk.Frame(body, bg=C.BG_C)
        top.pack(fill="x")

        badge = tk.Label(top, text=layer["level"], font=(F._FALLBACK, F.XS, "bold"), bg=color, fg=C.BG, padx=6, pady=2)
        badge.pack(side="left")

        tk.Label(top, text=f"  {layer['name']}", font=(F._PRIMARY, F.LG, "bold"), bg=C.BG_C, fg=C.FG_1).pack(side="left")

        # Status
        self._stats[key + "_status"] = tk.Label(top, text="Active", font=(F._FALLBACK, F.XS), bg=C.OK_D, fg=C.OK_L, padx=6, pady=2)
        self._stats[key + "_status"].pack(side="right")

        # Desc
        tk.Label(body, text=layer["desc"], font=(F._FALLBACK, F.SM), bg=C.BG_C, fg=C.FG_2, anchor="w").pack(fill="x", pady=(4, 0))

        # Usage info row
        stats_row = tk.Frame(body, bg=C.BG_C)
        stats_row.pack(fill="x", pady=(6, 0))

        count = self._counts.get(key, 0)
        self._stats[key + "_count"] = tk.Label(stats_row, text=f"{count:,} items", font=(F._FALLBACK, F.XS), bg=C.BG_C, fg=C.FG_3)
        self._stats[key + "_count"].pack(side="left")

        self._stats[key + "_ts"] = tk.Label(stats_row, text="—", font=(F._FALLBACK, F.XS), bg=C.BG_C, fg=C.FG_4)
        self._stats[key + "_ts"].pack(side="right")

        # Progress bar
        bar_frame = tk.Frame(body, bg=C.BG_C)
        bar_frame.pack(fill="x", pady=(4, 0))
        tk.Label(bar_frame, text=f"Usage  {count} / {layer['max_items']:,}", font=(F._FALLBACK, F.XS), bg=C.BG_C, fg=C.FG_3).pack(anchor="w")

        bg_bar = tk.Frame(bar_frame, bg=C.BORDER, height=5)
        bg_bar.pack(fill="x")

        pct = min(1.0, count / layer["max_items"])
        fill = tk.Frame(bg_bar, bg=color, height=5)
        fill.place(x=0, y=0)
        
        self._bars[key] = fill
        self._stats[key + "_max"] = layer["max_items"]
        self._stats[key + "_bg"]  = bg_bar

        # Resize/Update fill width immediately
        self.frame.after(100, lambda f=fill, b=bg_bar, p=pct: self._resize_bar(f, b, p))

    def _resize_bar(self, fill, bg_bar, pct) -> None:
        try:
            w = bg_bar.winfo_width() or 200
            fill.configure(width=int(w * pct))
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    def update_layer(self, key: str, count: int, status: str = "Active", last_ts: str = None) -> None:
        self._counts[key] = count
        
        fill = self._bars.get(key)
        bg   = self._stats.get(key + "_bg")
        if fill and bg:
            max_v = self._stats.get(key + "_max", 1)
            pct   = min(1.0, count / max_v)
            bar_w = bg.winfo_width() or 200
            fill.configure(width=int(bar_w * pct))

        cnt_lbl = self._stats.get(key + "_count")
        if cnt_lbl:
            max_v = self._stats.get(key + "_max", 0)
            cnt_lbl.configure(text=f"{count:,} items / {max_v:,}")

        sts_lbl = self._stats.get(key + "_status")
        if sts_lbl:
            color_map = {
                "Active":   (C.OK_D,   C.OK_L),
                "Idle":     (C.BG_C2,  C.FG_3),
                "Loading":  (C.BLUE_D, C.BLUE_L),
                "Error":    (C.ERR_D,  C.ERR_L),
            }
            bg_c, fg_c = color_map.get(status, (C.BG_C2, C.FG_3))
            sts_lbl.configure(text=status, bg=bg_c, fg=fg_c)

        ts_lbl = self._stats.get(key + "_ts")
        if ts_lbl and last_ts:
            ts_lbl.configure(text=f"Last: {last_ts}")

    # ─────────────────────────────────────────────────────────────────────────
    def _on_theme_changed(self) -> None:
        self.frame.configure(bg=C.BG_S)
        self.hdr.configure(bg=C.BG_C)
        self.lbl_title.configure(bg=C.BG_C, fg=C.FG_1)
        self.cv.configure(bg=C.BG_S)
        self._inner.configure(bg=C.BG_S)
        self.lbl_intro.configure(bg=C.BG_S, fg=C.FG_3)
        self.sep.configure(bg=C.BORDER)
        self._render_layers()
