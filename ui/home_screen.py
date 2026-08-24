"""
ui/home_screen.py — HELIOS v4.0 Premium Home Screen
=====================================================
First impression surface: greeting, quick-action cards, recent sessions.

Design:
  • Greeting — "Good [time], I'm HELIOS." in XXXL bold
  • Sub-headline — "How can I help you today?" in FG_2
  • Quick-action glass cards — 2×2 grid (New Note / Analyze File / Search Web / Schedule)
  • Recent sessions strip — if history is available
  • No heavy borders — elegant whitespace and typography do the work

The home screen is replaced immediately when the user sends their first message.
"""

from __future__ import annotations
import json
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from .theme import C, F, S, ThemeManager, hex_lerp
from .icon_manager import I


# ── Greeting by time-of-day ───────────────────────────────────────────────────
def _greeting() -> str:
    h = datetime.now().hour
    if h < 5:   return "Good evening"
    if h < 12:  return "Good morning"
    if h < 17:  return "Good afternoon"
    return "Good evening"


# ── Quick-action card definitions ─────────────────────────────────────────────
_QUICK_ACTIONS = [
    {
        "key":   "new_note",
        "icon":  I.NEW_NOTE,
        "title": "Write & Create",
        "desc":  "Draft, edit, or compose anything",
        "color": "BLUE",
    },
    {
        "key":   "analyze_file",
        "icon":  I.ANALYZE,
        "title": "Analyze & Explain",
        "desc":  "Attach a file or paste code",
        "color": "CYAN",
    },
    {
        "key":   "web_search",
        "icon":  I.WEB_SEARCH,
        "title": "Search the Web",
        "desc":  "Research topics in real-time",
        "color": "VIOLET",
    },
    {
        "key":   "schedule",
        "icon":  I.SCHEDULE,
        "title": "Plan & Organize",
        "desc":  "Tasks, schedules, and reminders",
        "color": "OK",
    },
]


class HomeScreen:
    """Premium home screen: greeting + quick-action cards + recent sessions."""

    def __init__(self, parent: tk.Widget,
                 on_action: callable = None,
                 on_load_session: callable = None,
                 on_trigger_file: callable = None) -> None:
        self._on_action       = on_action
        self._on_load_session = on_load_session
        self._on_trigger_file = on_trigger_file

        self.frame = tk.Frame(parent, bg=C.BG_S)
        self.frame.pack(fill="both", expand=True)

        self._build()
        ThemeManager.add_listener(self._on_theme_changed)

    # ─────────────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        for w in self.frame.winfo_children():
            w.destroy()

        # Outer centering padder
        self.container = tk.Frame(self.frame, bg=C.BG_S)
        self.container.pack(fill="both", expand=True, padx=24, pady=(40, 16))
        self.container.bind("<Configure>", self._on_container_resize)

        # ── Greeting ─────────────────────────────────────────────────────────
        greeting_text = f"{_greeting()}, I'm HELIOS."
        self.greeting_lbl = tk.Label(
            self.container,
            text=greeting_text,
            font=(F._PRIMARY, F.XXL, "bold"),
            bg=C.BG_S, fg=C.FG_1,
            wraplength=380, justify="left",
        )
        self.greeting_lbl.pack(anchor="w", pady=(0, 4))

        # Sub-headline
        self.sub_lbl = tk.Label(
            self.container,
            text="What would you like to accomplish today?",
            font=(F._PRIMARY, F.MD),
            bg=C.BG_S, fg=C.FG_2,
            wraplength=380, justify="left",
        )
        self.sub_lbl.pack(anchor="w", pady=(0, 20))

        # ── Quick-action cards — 2-column grid ───────────────────────────────
        grid = tk.Frame(self.container, bg=C.BG_S)
        grid.pack(fill="x", pady=(0, 20))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self._action_cards: list[dict] = []
        for i, qa in enumerate(_QUICK_ACTIONS):
            row, col = divmod(i, 2)
            self._make_action_card(grid, row=row, col=col, qa=qa)

        # ── Recent sessions (if any) ──────────────────────────────────────────
        self._try_render_recent_sessions()

    def _on_container_resize(self, e) -> None:
        try:
            w = max(160, e.width - 20)
            self.greeting_lbl.configure(wraplength=w)
            self.sub_lbl.configure(wraplength=w)

            # Strict 2x2 grid layout width calculation
            card_w = max(90, (e.width - 28) // 2)

            for i, item in enumerate(self._action_cards):
                row, col = divmod(i, 2)
                item["card"].grid(row=row, column=col, padx=4, pady=4, sticky="ew")
                item["title"].configure(wraplength=card_w - 20)
                item["desc"].configure(wraplength=card_w - 20)
        except Exception:
            pass

    def _make_action_card(self, grid: tk.Widget, row: int, col: int,
                           qa: dict) -> None:
        """Build one premium quick-action glass card."""
        color_key = qa["color"]
        accent    = getattr(C, color_key)
        dim_key   = color_key + "_DIM" if hasattr(C, color_key + "_DIM") else "GLASS_3"
        bg_dim    = getattr(C, dim_key) if hasattr(C, dim_key) else C.GLASS_3

        # Card frame — GLASS_3 surface with thin accent border
        card = tk.Frame(grid,
                         bg=C.GLASS_3,
                         highlightthickness=1,
                         highlightbackground=C.GLASS_BD_3,
                         cursor="hand2")
        card.grid(row=row, column=col, padx=4, pady=4, sticky="ew")

        body = tk.Frame(card, bg=C.GLASS_3, padx=12, pady=10)
        body.pack(fill="both", expand=True)

        # Icon
        lbl_icon = tk.Label(body, text=qa["icon"],
                             font=(F._FALLBACK, F.LG),
                             bg=C.GLASS_3, fg=accent)
        lbl_icon.pack(anchor="w", pady=(0, 2))

        # Title
        lbl_title = tk.Label(body, text=qa["title"],
                              font=(F._PRIMARY, F.SM, "bold"),
                              bg=C.GLASS_3, fg=C.FG_1,
                              justify="left", anchor="w")
        lbl_title.pack(anchor="w", pady=(0, 2), fill="x")

        # Description
        lbl_desc = tk.Label(body, text=qa["desc"],
                             font=(F._FALLBACK, F.XS),
                             bg=C.GLASS_3, fg=C.FG_2,
                             justify="left", anchor="w")
        lbl_desc.pack(anchor="w", pady=(2, 0), fill="x")

        # Hover / active effects (subtle warm gold perimeter reflection)
        gold_glow = C.EDGE_IDLE
        def _enter(e):
            card.configure(highlightbackground=gold_glow, bg=bg_dim)
            body.configure(bg=bg_dim)
            lbl_icon.configure(bg=bg_dim)
            lbl_title.configure(bg=bg_dim)
            lbl_desc.configure(bg=bg_dim)

        def _leave(e):
            card.configure(highlightbackground=C.GLASS_BD_3, bg=C.GLASS_3)
            body.configure(bg=C.GLASS_3)
            lbl_icon.configure(bg=C.GLASS_3)
            lbl_title.configure(bg=C.GLASS_3)
            lbl_desc.configure(bg=C.GLASS_3)

        def _click(e, key=qa["key"]):
            if self._on_action:
                self._on_action(key)

        for w in (card, body, lbl_icon, lbl_title, lbl_desc):
            w.bind("<Enter>",           _enter)
            w.bind("<Leave>",           _leave)
            w.bind("<ButtonRelease-1>", _click)

        self._action_cards.append({
            "card": card, "body": body,
            "icon": lbl_icon, "title": lbl_title, "desc": lbl_desc,
            "color": color_key,
        })

    def _try_render_recent_sessions(self) -> None:
        """Render recent chat sessions strip (max 3) if available."""
        try:
            from core.system import paths_manager
            sessions_dir = paths_manager.sessions_dir
            if not sessions_dir.exists():
                return

            sessions = sorted(sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime,
                               reverse=True)[:3]
            if not sessions:
                return

            # Section header
            tk.Label(self.container, text="Recent Sessions",
                      font=(F._PRIMARY, F.SM, "bold"),
                      bg=C.BG_S, fg=C.FG_2).pack(anchor="w", pady=(4, 6))

            for path in sessions:
                self._make_session_item(path)
        except Exception:
            pass   # No sessions or paths_manager not available — silent fail

    def _make_session_item(self, path: Path) -> None:
        """Render a single recent session as a compact row."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            title     = data.get("title", path.stem)
            timestamp = data.get("updated_at", "")
            session_id = path.stem

            if timestamp:
                try:
                    dt  = datetime.fromisoformat(timestamp)
                    ts  = dt.strftime("%b %d, %I:%M %p")
                except Exception:
                    ts = timestamp[:16]
            else:
                ts = ""

            row = tk.Frame(self.container, bg=C.GLASS_3,
                            highlightthickness=1,
                            highlightbackground=C.GLASS_BD_3,
                            cursor="hand2")
            row.pack(fill="x", pady=2)

            inner = tk.Frame(row, bg=C.GLASS_3, padx=12, pady=8)
            inner.pack(fill="x")

            lbl_t = tk.Label(inner, text=title,
                              font=(F._FALLBACK, F.SM),
                              bg=C.GLASS_3, fg=C.FG_1)
            lbl_t.pack(side="left")

            lbl_s = tk.Label(inner, text=ts,
                              font=(F._FALLBACK, F.XS),
                              bg=C.GLASS_3, fg=C.FG_3)
            lbl_s.pack(side="right")

            def _enter(e): row.configure(highlightbackground=C.BLUE)
            def _leave(e): row.configure(highlightbackground=C.GLASS_BD_3)
            def _click(e, sid=session_id):
                if self._on_load_session:
                    self._on_load_session(sid)

            for w in (row, inner, lbl_t, lbl_s):
                w.bind("<Enter>",           _enter)
                w.bind("<Leave>",           _leave)
                w.bind("<ButtonRelease-1>", _click)

        except Exception:
            pass

    def refresh(self, agent=None) -> None:
        """Refresh home screen view."""
        try:
            self._build()
        except Exception:
            pass

    def _on_theme_changed(self) -> None:
        try:
            self.frame.configure(bg=C.BG_S)
            self.container.configure(bg=C.BG_S)
            self.greeting_lbl.configure(bg=C.BG_S, fg=C.FG_1)
            self.sub_lbl.configure(bg=C.BG_S, fg=C.FG_2)

            for entry in self._action_cards:
                entry["card"].configure(bg=C.GLASS_3, highlightbackground=C.GLASS_BD_3)
                entry["body"].configure(bg=C.GLASS_3)
                entry["top"].configure(bg=C.GLASS_3)
                entry["icon"].configure(bg=C.GLASS_3, fg=getattr(C, entry["color"]))
                entry["title"].configure(bg=C.GLASS_3, fg=C.FG_1)
                entry["desc"].configure(bg=C.GLASS_3, fg=C.FG_2)
        except Exception:
            pass
