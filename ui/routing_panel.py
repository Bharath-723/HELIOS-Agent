"""
ui/routing_panel.py — HELIOS CAHRA Routing Visualization
=========================================================
Reads LIVE diagnostics from data/diagnostics/*.json.
"""

from __future__ import annotations
import json
import os
import tkinter as tk
from pathlib import Path
from datetime import datetime
from .theme import C, F, S, ThemeManager
from .icon_manager import I

_DIAG_PATHS = [
    Path("data/diagnostics"),
    Path("data/diagnostics/"),
]


class RoutingPanel:
    """Live CAHRA routing decision visualization."""

    def __init__(self, parent: tk.Widget) -> None:
        self.frame = tk.Frame(parent, bg=C.BG_S)
        self._base_dir: Path | None = self._find_diag_dir()
        self._last_data = {}
        
        self._build()
        self.refresh()

        ThemeManager.add_listener(self._on_theme_changed)

    def _find_diag_dir(self) -> Path | None:
        for p in _DIAG_PATHS:
            if p.exists():
                return p
        cwd = Path(os.getcwd())
        for p in _DIAG_PATHS:
            full = cwd / p
            if full.exists():
                return full
        return None

    # ─────────────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        self.hdr = tk.Frame(self.frame, bg=C.BG_C, height=48)
        self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)

        self.lbl_title = tk.Label(self.hdr, text="  ⚡ CAHRA Routing",
                                  font=(F._PRIMARY, F.LG, "bold"),
                                  bg=C.BG_C, fg=C.FG_1)
        self.lbl_title.pack(side="left", pady=14)

        self._ref_btn = tk.Label(self.hdr, text=f"{I.REFRESH} Refresh",
                                 font=(F._FALLBACK, F.SM),
                                 bg=C.BORDER_2, fg=C.FG_2,
                                 cursor="hand2", padx=8, pady=4)
        self._ref_btn.pack(side="right", padx=10)
        self._ref_btn.bind("<ButtonRelease-1>", lambda e: self.refresh())

        # Scrollable content
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

    # ─────────────────────────────────────────────────────────────────────────
    def refresh(self) -> None:
        for w in self._inner.winfo_children():
            w.destroy()

        self._last_data = self._load_latest() or {}
        if not self._last_data:
            self._no_data()
            return
        self._render(self._last_data)

    def _load_latest(self) -> dict | None:
        if not self._base_dir:
            return None
        candidates = ["decision_snapshot.json", "routing_log.json",
                      "cahra_decision.json", "last_decision.json"]
        for name in candidates:
            f = self._base_dir / name
            if f.exists():
                try:
                    return json.loads(f.read_text(encoding="utf-8"))
                except Exception:
                    pass
        jsons = list(self._base_dir.glob("*.json"))
        if jsons:
            jsons.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            try:
                return json.loads(jsons[0].read_text(encoding="utf-8"))
            except Exception:
                pass
        return None

    def _no_data(self) -> None:
        self.lbl_info = tk.Label(self._inner,
                                 text=f"\n{I.INFO}  No routing diagnostics available.\n\n"
                                      "Diagnostics are written to data/diagnostics/ after\n"
                                      "the first CAHRA routing decision.",
                                 font=(F._FALLBACK, F.SM),
                                 bg=C.BG_S, fg=C.FG_3,
                                 justify="center", pady=20)
        self.lbl_info.pack(expand=True)

    def _render(self, data: dict) -> None:
        pad = {"padx": 12, "pady": 4}

        self._section("Decision", self._inner)

        action     = data.get("action", data.get("decision", "unknown"))
        confidence = data.get("confidence", data.get("score", 0))
        latency    = data.get("latency_ms", data.get("elapsed_ms", None))
        timestamp  = data.get("timestamp", data.get("ts", ""))

        dec_card = tk.Frame(self._inner, bg=C.BG_C, highlightthickness=1, highlightbackground=C.BORDER)
        dec_card.pack(fill="x", **pad)

        row = tk.Frame(dec_card, bg=C.BG_C)
        row.pack(fill="x", padx=10, pady=(8, 4))

        tk.Label(row, text="Action", font=(F._FALLBACK, F.XS), bg=C.BG_C, fg=C.FG_3).pack(side="left")
        tk.Label(row, text=str(action), font=(F._FALLBACK, F.SM, "bold"), bg=C.BG_C, fg=C.BLUE).pack(side="left", padx=8)

        if latency is not None:
            tk.Label(row, text=f"⏱ {latency:.0f}ms", font=(F._FALLBACK, F.XS), bg=C.BG_C, fg=C.FG_3).pack(side="right")

        if confidence:
            conf_f = float(confidence)
            bar_w  = 240
            filled = int(bar_w * conf_f)
            bar_frame = tk.Frame(dec_card, bg=C.BG_C)
            bar_frame.pack(fill="x", padx=10, pady=(0, 8))

            tk.Label(bar_frame, text=f"Confidence  {conf_f:.0%}", font=(F._FALLBACK, F.XS), bg=C.BG_C, fg=C.FG_3).pack(anchor="w")
            bg_bar = tk.Frame(bar_frame, bg=C.BORDER, height=6, width=bar_w)
            bg_bar.pack(anchor="w")

            fill_color = (C.OK if conf_f > 0.8 else C.WARN if conf_f > 0.5 else C.ERR)
            fill_bar = tk.Frame(bg_bar, bg=fill_color, height=6, width=filled)
            fill_bar.place(x=0, y=0)

        if timestamp:
            tk.Label(dec_card, text=f"Updated: {str(timestamp)[:19]}", font=(F._FALLBACK, F.XS), bg=C.BG_C, fg=C.FG_4, anchor="w").pack(anchor="w", padx=10, pady=(0, 6))

        candidates = data.get("candidates", data.get("scores", []))
        if candidates:
            self._section("Candidate Ranking", self._inner)
            for item in (candidates if isinstance(candidates, list) else [{"action": k, "score": v} for k, v in candidates.items()]):
                self._candidate_row(item)

        constraints = data.get("constraints", data.get("constraint_triggers", []))
        if constraints:
            self._section("Active Constraints", self._inner)
            for c in (constraints if isinstance(constraints, list) else [constraints]):
                self._constraint_row(c)

        explanation = data.get("explanation", data.get("reason", ""))
        if explanation:
            self._section("Explanation", self._inner)
            tk.Label(self._inner, text=str(explanation), font=(F._FALLBACK, F.SM), bg=C.BG_S, fg=C.FG_2, wraplength=300, justify="left", padx=12, pady=6).pack(fill="x")

    def _section(self, title: str, parent: tk.Widget) -> None:
        tk.Label(parent, text=f"  {title}", font=(F._FALLBACK, F.XS), bg=C.BG_S, fg=C.FG_3, pady=4).pack(fill="x")
        tk.Frame(parent, bg=C.BORDER, height=1).pack(fill="x", padx=8, pady=(0, 4))

    def _candidate_row(self, item: dict) -> None:
        action = item.get("action", item.get("name", str(item)))
        score  = float(item.get("score", item.get("confidence", 0)))

        row = tk.Frame(self._inner, bg=C.BG_S)
        row.pack(fill="x", padx=12, pady=1)
        tk.Label(row, text=str(action), font=(F._FALLBACK, F.SM), bg=C.BG_S, fg=C.FG_2, width=20, anchor="w").pack(side="left")
        
        bar = tk.Frame(row, bg=C.BORDER_2, height=4, width=100)
        bar.pack(side="left", padx=4)
        tk.Frame(bar, bg=C.BLUE, height=4, width=int(100 * score)).place(x=0, y=0)
        
        tk.Label(row, text=f"{score:.2f}", font=(F._FALLBACK, F.XS), bg=C.BG_S, fg=C.FG_3).pack(side="left")

    def _constraint_row(self, c) -> None:
        row = tk.Frame(self._inner, bg=C.BG_S)
        row.pack(fill="x", padx=12, pady=1)
        if isinstance(c, dict):
            level = c.get("level", "allowed")
            name  = c.get("name", c.get("constraint", str(c)))
        else:
            level = "active"
            name  = str(c)
        color = {"forbidden": C.ERR, "discouraged": C.WARN, "preferred": C.OK, "allowed": C.FG_3}.get(level, C.FG_3)
        tk.Label(row, text=f"◈ {name}", font=(F._FALLBACK, F.SM), bg=C.BG_S, fg=color).pack(side="left")
        tk.Label(row, text=level, font=(F._FALLBACK, F.XS), bg=C.BG_S, fg=color).pack(side="right")

    # ─────────────────────────────────────────────────────────────────────────
    def _on_theme_changed(self) -> None:
        self.frame.configure(bg=C.BG_S)
        self.hdr.configure(bg=C.BG_C)
        self.lbl_title.configure(bg=C.BG_C, fg=C.FG_1)
        self._ref_btn.configure(bg=C.BORDER_2, fg=C.FG_2)
        self.cv.configure(bg=C.BG_S)
        self._inner.configure(bg=C.BG_S)
        self.refresh()
