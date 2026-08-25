"""
ui/diagnostics_panel.py — HELIOS Activity/Statistics Panel
===========================================================
Reference Image 3 — clean glass statistics layout.

Compact glass stat cards with:
  - SESSION stats (actions, verified, failed, recovery)
  - LLM stats (model, latency, requests)
  - DESKTOP stats (app, screen, last action)
  - COMMERCE stats (searches, products, verified)
  - SCREEN PRIVACY indicator

Usage:
    panel = DiagnosticsPanel(parent)
    panel.frame.pack(fill="both", expand=True)
    panel.update_session(actions=5, verified=5, failed=0)
"""

from __future__ import annotations
import tkinter as tk
from .theme import C, F, ThemeManager
from .stat_card import StatCard


class DiagnosticsPanel:
    """
    Activity statistics panel — clean 4-card high-value information hierarchy.
    """

    def __init__(self, parent: tk.Widget) -> None:
        self.frame = tk.Frame(parent, bg=C.BG_S)
        self._latencies: list[float] = []
        self._request_count = 0

        # Scrollable container
        self._canvas = tk.Canvas(self.frame, bg=C.BG_S, highlightthickness=0)
        self._vsb    = tk.Scrollbar(self.frame, orient="vertical",
                                    command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)

        self._canvas.pack(side="left", fill="both", expand=True)
        self._vsb.pack(side="right", fill="y")

        self._inner = tk.Frame(self._canvas, bg=C.BG_S)
        self._win   = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", lambda e: self._update_canvas_window())
        self._canvas.bind("<Configure>", lambda e: self._update_canvas_window())
        self.frame.bind("<Enter>", lambda e: self._bind_mousewheel_all(self._inner))
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)

        self._build()
        ThemeManager.add_listener(self._on_theme_changed)

    def _on_mousewheel(self, event) -> None:
        try:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _bind_mousewheel_all(self, widget) -> None:
        try:
            widget.bind("<MouseWheel>", self._on_mousewheel, "+")
            for child in widget.winfo_children():
                self._bind_mousewheel_all(child)
        except Exception:
            pass

    def _update_canvas_window(self) -> None:
        try:
            self.frame.update_idletasks()
            w = self._canvas.winfo_width()
            h = max(self._inner.winfo_reqheight(), self.frame.winfo_height())
            if w > 10 and h > 10:
                self._canvas.itemconfig(self._win, width=w)
                self._canvas.configure(scrollregion=(0, 0, w, self._inner.winfo_reqheight()))
        except Exception:
            pass

    def _build(self) -> None:
        pad = 16

        # ── Header ─────────────────────────────────────────────────────────────
        hdr = tk.Frame(self._inner, bg=C.BG_S)
        hdr.pack(fill="x", padx=pad, pady=(16, 12))

        tk.Label(hdr, text="ACTIVITY",
                 font=(F._PRIMARY, F.LG, "bold"),
                 bg=C.BG_S, fg=C.FG_1).pack(side="left")

        self._ts_lbl = tk.Label(hdr, text="Live Telemetry",
                                 font=(F._FALLBACK, F.XS),
                                 bg=C.BG_S, fg=C.FG_3)
        self._ts_lbl.pack(side="right")

        # ── Card 1: AGENT STATUS ────────────────────────────────────────────────
        tk.Label(self._inner, text="AGENT STATUS",
                 font=(F._FALLBACK, F.XS, "bold"),
                 bg=C.BG_S, fg=C.FG_3,
                 anchor="w").pack(fill="x", padx=pad, pady=(0, 6))

        row1 = tk.Frame(self._inner, bg=C.BG_S)
        row1.pack(fill="x", padx=pad, pady=(0, 14))

        self._agent_card = StatCard(row1, title="AGENT",
                                    primary="● IDLE", primary_label="Status",
                                    accent_color=C.STATE_IDLE)
        self._agent_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._session_card = StatCard(row1, title="SESSION",
                                      primary="0", primary_label="Actions Completed",
                                      secondary="0%", secondary_label="Verified",
                                      accent_color=C.OK)
        self._session_card.pack(side="left", fill="both", expand=True)

        # ── Card 2: LLM PERFORMANCE ─────────────────────────────────────────────
        tk.Label(self._inner, text="LLM PERFORMANCE",
                 font=(F._FALLBACK, F.XS, "bold"),
                 bg=C.BG_S, fg=C.FG_3,
                 anchor="w").pack(fill="x", padx=pad, pady=(4, 6))

        row2 = tk.Frame(self._inner, bg=C.BG_S)
        row2.pack(fill="x", padx=pad, pady=(0, 14))

        self._model_card = StatCard(row2, title="MODEL",
                                    primary="gemma3", primary_label="Active LLM",
                                    secondary="● LOCAL", accent_color=C.OK)
        self._model_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._lat_card = StatCard(row2, title="LATENCY",
                                  primary="—", primary_label="ms avg",
                                  secondary="0 requests", secondary_label="Total",
                                  accent_color=C.CYAN)
        self._lat_card.pack(side="left", fill="both", expand=True)

        # ── Card 3: AUTOMATION & SCREEN ─────────────────────────────────────────
        tk.Label(self._inner, text="AUTOMATION & SCREEN",
                 font=(F._FALLBACK, F.XS, "bold"),
                 bg=C.BG_S, fg=C.FG_3,
                 anchor="w").pack(fill="x", padx=pad, pady=(4, 6))

        row3 = tk.Frame(self._inner, bg=C.BG_S)
        row3.pack(fill="x", padx=pad, pady=(0, 14))

        self._app_card = StatCard(row3, title="ACTIVE APP",
                                  primary="HELIOS", primary_label="Foreground Window",
                                  accent_color=C.BLUE)
        self._app_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._screen_card = StatCard(row3, title="PRIVACY GUARD",
                                     primary="● ON-DEVICE", primary_label="Local Sandbox",
                                     accent_color=C.OK)
        self._screen_card.pack(side="left", fill="both", expand=True)

        # ── Section 4: RECENT ACTIVITY TIMELINE ─────────────────────────────────
        tk.Label(self._inner, text="RECENT ACTIVITY",
                 font=(F._FALLBACK, F.XS, "bold"),
                 bg=C.BG_S, fg=C.FG_3,
                 anchor="w").pack(fill="x", padx=pad, pady=(4, 6))

        self._timeline_frame = tk.Frame(self._inner, bg=C.GLASS_3, padx=12, pady=10,
                                        highlightthickness=1, highlightbackground=C.GLASS_BD_3)
        self._timeline_frame.pack(fill="x", padx=pad, pady=(0, 16))

        self._timeline_items: list[str] = [
            "● Initialized HELIOS Material System",
            "● Connected to Local Model Service (gemma3)",
            "● Privacy Guard Armed & Ready"
        ]
        self._render_timeline()

    def _render_timeline(self) -> None:
        for w in self._timeline_frame.winfo_children():
            w.destroy()
        for item in self._timeline_items[-5:]:
            row = tk.Frame(self._timeline_frame, bg=C.GLASS_3)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=item, font=(F._FALLBACK, F.SM), bg=C.GLASS_3, fg=C.FG_2, anchor="w").pack(side="left")

    def add_activity_log(self, log_entry: str) -> None:
        self._timeline_items.append(f"● {log_entry}")
        self._render_timeline()

    # ─────────────────────────────────────────────────────────────────────────
    def update_session(self, actions: int = 0, verified: int = 0,
                        failed: int = 0, recovery: int = 0,
                        state: str = "idle", state_label: str = "Desktop Agent") -> None:
        pct = f"{int((verified/max(actions,1))*100)}%" if actions > 0 else "0%"
        try:
            self._session_card.update(primary=str(actions), secondary=pct)
            dot_color = {"working": C.STATE_WORKING, "thinking": C.STATE_THINKING,
                         "error": C.STATE_ERROR, "success": C.STATE_SUCCESS,
                         "idle": C.STATE_IDLE}.get(state, C.STATE_IDLE)
            self._agent_card.update(primary=f"●  {state.upper()}", primary_label=state_label)
        except Exception:
            pass

    def update_llm(self, model: str = "", latency_ms: float = 0,
                   requests: int = 0, is_local: bool = True) -> None:
        try:
            self._model_card.update(primary=model or "gemma3",
                                    secondary="● LOCAL" if is_local else "☁ CLOUD")
            if requests > 0 and latency_ms > 0:
                self._lat_card.update(primary=f"{latency_ms:.0f}", secondary=f"{requests} requests")
            elif self._latencies:
                avg_lat = sum(self._latencies) / len(self._latencies)
                self._lat_card.update(primary=f"{avg_lat:.0f}", secondary=f"{len(self._latencies)} requests")
            else:
                self._lat_card.update(primary="—", secondary="0 requests")
        except Exception:
            pass

    def update_screen(self, app_name: str = "", is_local: bool = True) -> None:
        try:
            label = "● ON-DEVICE" if is_local else "☁ CLOUD"
            self._screen_card.update(primary=label)
            if app_name:
                self._app_card.update(primary=app_name[:24])
        except Exception:
            pass

    def update_commerce(self, searches: int = 0, products: int = 0,
                         payments: int = 0) -> None:
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def refresh(self) -> None:
        try:
            self._update_canvas_window()
        except Exception:
            pass

    def update_model_name(self, model: str) -> None:
        try:
            self._model_card.update(primary=model)
        except Exception:
            pass

    def record_latency(self, elapsed_ms: float) -> None:
        try:
            self._latencies.append(elapsed_ms)
            self._request_count += 1
            avg_lat = sum(self._latencies) / len(self._latencies)
            self._lat_card.update(primary=f"{avg_lat:.0f}", secondary=f"{self._request_count} requests")
        except Exception:
            pass

    def update_metrics(self, *args, **kwargs) -> None:
        pass

    def _on_theme_changed(self) -> None:
        try:
            self.frame.configure(bg=C.BG_S)
            self._canvas.configure(bg=C.BG_S)
            self._inner.configure(bg=C.BG_S)
        except Exception:
            pass
