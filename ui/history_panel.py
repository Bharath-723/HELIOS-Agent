"""
ui/history_panel.py — HELIOS v4.0 Chat History Panel
======================================================
Premium scrollable session timeline with glass cards, search, and soft-delete.

Design:
  • GLASS_2 header surface
  • Frosted glass search bar
  • Session cards: GLASS_3 with left accent strip (BLUE)
  • Hover: card border illuminates to BLUE
  • Delete: trash icon appears on hover (not always visible)
  • Date grouping: "Today", "Yesterday", "Earlier"
"""

from __future__ import annotations
import tkinter as tk
from datetime import datetime, date, timedelta
from .theme import C, F, S, ThemeManager, hex_lerp
from .icon_manager import I


def _date_group(ts_str: str) -> str:
    """Return display group label for a session timestamp string."""
    if not ts_str:
        return "Earlier"
    try:
        dt   = datetime.fromisoformat(ts_str.replace(" ", "T")[:19])
        diff = date.today() - dt.date()
        if diff.days == 0:
            return "Today"
        if diff.days == 1:
            return "Yesterday"
        if diff.days <= 7:
            return "This Week"
        return dt.strftime("%B %Y")
    except Exception:
        return "Earlier"


class HistoryPanel:
    """Scrollable session history panel — glass cards with date grouping."""

    def __init__(self, parent: tk.Widget,
                 on_load: callable,
                 on_new:  callable,
                 on_clear: callable) -> None:
        self._on_load  = on_load
        self._on_new   = on_new
        self._on_clear = on_clear
        self._agent    = None
        self._sessions: list[dict] = []

        self.frame = tk.Frame(parent, bg=C.BG_S)
        self._build()
        ThemeManager.add_listener(self._on_theme_changed)

    # ─────────────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # ── Header ───────────────────────────────────────────────────────────
        self.hdr = tk.Frame(self.frame, bg=C.GLASS_2, height=52)
        self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)

        self.lbl_title = tk.Label(self.hdr,
                                   text=f"  {I.HISTORY}  Chat History",
                                   font=(F._PRIMARY, F.LG, "bold"),
                                   bg=C.GLASS_2, fg=C.FG_1)
        self.lbl_title.pack(side="left", pady=14)

        # "New Chat" button
        self.btn_new = tk.Label(self.hdr, text="+ New Chat",
                                 font=(F._FALLBACK, F.XS, "bold"),
                                 bg=C.BLUE_D, fg=C.FG_1,
                                 cursor="hand2", padx=10, pady=4)
        self.btn_new.pack(side="right", padx=10)
        self.btn_new.bind("<ButtonRelease-1>", lambda e: self._on_new())

        def _new_enter(e): self.btn_new.configure(bg=C.BLUE)
        def _new_leave(e): self.btn_new.configure(bg=C.BLUE_D)
        self.btn_new.bind("<Enter>", _new_enter)
        self.btn_new.bind("<Leave>", _new_leave)

        # ── Header separator ─────────────────────────────────────────────────
        tk.Frame(self.frame, bg=C.GLASS_BD_2, height=1).pack(fill="x")

        # ── Search bar ───────────────────────────────────────────────────────
        self.search_row = tk.Frame(self.frame, bg=C.BG_S)
        self.search_row.pack(fill="x", padx=8, pady=8)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._filter())

        self.search_entry = tk.Entry(self.search_row,
                                      textvariable=self._search_var,
                                      font=(F._FALLBACK, F.SM),
                                      bg=C.GLASS_3, fg=C.FG_1,
                                      relief="flat", bd=6,
                                      insertbackground=C.BLUE)
        self.search_entry.insert(0, f"{I.SEARCH}  Search sessions…")
        self.search_entry.pack(fill="x", ipady=4)

        def _sf(e):
            if self.search_entry.get().startswith(I.SEARCH):
                self.search_entry.delete(0, tk.END)
        def _sb(e):
            if not self.search_entry.get():
                self.search_entry.insert(0, f"{I.SEARCH}  Search sessions…")

        self.search_entry.bind("<FocusIn>",  _sf)
        self.search_entry.bind("<FocusOut>", _sb)

        # ── Session list ─────────────────────────────────────────────────────
        self.lf = tk.Frame(self.frame, bg=C.BG_S)
        self.lf.pack(fill="both", expand=True)
        self.lf.rowconfigure(0, weight=1)
        self.lf.columnconfigure(0, weight=1)

        self.cv  = tk.Canvas(self.lf, bg=C.BG_S, highlightthickness=0)
        self.vsb = tk.Scrollbar(self.lf, orient="vertical", command=self.cv.yview)
        self.cv.configure(yscrollcommand=self.vsb.set)
        self.cv.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")

        self._inner = tk.Frame(self.cv, bg=C.BG_S)
        self._win   = self.cv.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>",
                         lambda e: self.cv.configure(scrollregion=self.cv.bbox("all")))
        self.cv.bind("<Configure>",
                     lambda e: self.cv.itemconfig(self._win, width=e.width))

        def _scroll(e): self.cv.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self.cv.bind("<MouseWheel>",    _scroll)
        self._inner.bind("<MouseWheel>", _scroll)

        # ── Footer ───────────────────────────────────────────────────────────
        self.sep = tk.Frame(self.frame, bg=C.BORDER, height=1)
        self.sep.pack(fill="x")

        self.btn_clear = tk.Label(self.frame, text="Clear All History",
                                   font=(F._FALLBACK, F.SM),
                                   bg=C.BG_S, fg=C.ERR,
                                   cursor="hand2", pady=8)
        self.btn_clear.pack()
        self.btn_clear.bind("<ButtonRelease-1>", lambda e: self._on_clear())

    # ─────────────────────────────────────────────────────────────────────────
    def refresh(self, agent) -> None:
        self._agent = agent
        if not agent:
            return
        # Render existing cached sessions immediately
        self._render(self._sessions)
        # Background fetch to avoid blocking UI main thread
        import threading
        def _bg_fetch():
            try:
                sessions = agent.history.get_all() or []
                self._sessions = sessions
                self.frame.after(0, lambda: self._render(sessions))
            except Exception:
                pass
        threading.Thread(target=_bg_fetch, daemon=True).start()

    def _filter(self) -> None:
        if not hasattr(self, "_inner"):
            return
        q = self._search_var.get().lower().strip()
        if not q or q.startswith(I.SEARCH.lower()):
            self._render(self._sessions)
            return
        filtered = [s for s in self._sessions if q in s.get("title", "").lower()]
        self._render(filtered)

    # ─────────────────────────────────────────────────────────────────────────
    def _render(self, sessions: list[dict]) -> None:
        for w in self._inner.winfo_children():
            w.destroy()

        if not sessions:
            tk.Label(self._inner, text="No sessions yet.\nStart a conversation to see history here.",
                      font=(F._FALLBACK, F.SM),
                      bg=C.BG_S, fg=C.FG_3,
                      pady=32, justify="center").pack()
            return

        # Group by date
        grouped: dict[str, list[dict]] = {}
        for s in sessions:
            group = _date_group(s.get("started", ""))
            grouped.setdefault(group, []).append(s)

        for group_label in ["Today", "Yesterday", "This Week"]:
            if group_label in grouped:
                self._group_header(group_label)
                for s in grouped[group_label]:
                    self._session_card(s)

        for label, items in grouped.items():
            if label not in ("Today", "Yesterday", "This Week"):
                self._group_header(label)
                for s in items:
                    self._session_card(s)

        # Bind scroll recursively after render
        def _bind(w):
            w.bind("<MouseWheel>",
                   lambda e: self.cv.yview_scroll(int(-1 * (e.delta / 120)), "units"))
            for c in w.winfo_children():
                _bind(c)
        self._inner.after(50, lambda: _bind(self._inner))

    def _group_header(self, text: str) -> None:
        """Date group label — muted, with underline separator."""
        row = tk.Frame(self._inner, bg=C.BG_S)
        row.pack(fill="x", padx=10, pady=(12, 4))
        tk.Label(row, text=text,
                  font=(F._PRIMARY, F.XS, "bold"),
                  bg=C.BG_S, fg=C.FG_3).pack(side="left")
        tk.Frame(row, bg=C.GLASS_BD_2, height=1).pack(side="left", fill="x",
                                                       expand=True, padx=(8, 0))

    def _session_card(self, s: dict) -> None:
        """One session card: GLASS_3 surface, accent strip, hover delete."""
        sid   = s.get("id", "")
        title = s.get("title", sid)[:42]
        ts    = s.get("started", "")[:16].replace("T", " ")
        count = s.get("message_count", 0)

        # Outer container (provides 3-sided spacing)
        card = tk.Frame(self._inner,
                         bg=C.GLASS_3,
                         highlightthickness=1,
                         highlightbackground=C.GLASS_BD_3,
                         cursor="hand2")
        card.pack(fill="x", padx=8, pady=3)

        # Left accent strip (BLUE — soft, not neon)
        accent = tk.Frame(card, bg=C.BLUE_DIM, width=3)
        accent.pack(side="left", fill="y")

        # Body
        body = tk.Frame(card, bg=C.GLASS_3)
        body.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        lbl_t = tk.Label(body, text=title,
                          font=(F._FALLBACK, F.SM, "bold"),
                          bg=C.GLASS_3, fg=C.FG_1, anchor="w")
        lbl_t.pack(fill="x")

        lbl_s = tk.Label(body,
                          text=f"{ts}  ·  {count} msg",
                          font=(F._FALLBACK, F.XS),
                          bg=C.GLASS_3, fg=C.FG_3, anchor="w")
        lbl_s.pack(fill="x")

        # Delete icon (right side) — always present but subtle
        lbl_del = tk.Label(card, text=I.TRASH,
                            font=(F._FALLBACK, F.SM),
                            bg=C.GLASS_3, fg=C.FG_4,
                            cursor="hand2", padx=10)
        lbl_del.pack(side="right")

        # Hover: illuminate card
        def _enter(e):
            card.configure(highlightbackground=C.BLUE)
            accent.configure(bg=C.BLUE)
            lbl_del.configure(fg=C.ERR)

        def _leave(e):
            card.configure(highlightbackground=C.GLASS_BD_3)
            accent.configure(bg=C.BLUE_DIM)
            lbl_del.configure(fg=C.FG_4)

        def _click(e): self._on_load(sid)

        def _del(e):
            if self._agent and hasattr(self._agent.history, "soft_delete"):
                self._agent.history.soft_delete(sid)
                self.refresh(self._agent)

        lbl_del.bind("<ButtonRelease-1>", _del)

        for w in (card, body, lbl_t, lbl_s):
            w.bind("<Enter>",           _enter)
            w.bind("<Leave>",           _leave)
            w.bind("<ButtonRelease-1>", _click)

    # ─────────────────────────────────────────────────────────────────────────
    def _on_theme_changed(self) -> None:
        self.frame.configure(bg=C.BG_S)
        self.hdr.configure(bg=C.GLASS_2)
        self.lbl_title.configure(bg=C.GLASS_2, fg=C.FG_1)
        self.search_row.configure(bg=C.BG_S)
        self.search_entry.configure(bg=C.GLASS_3, fg=C.FG_1, insertbackground=C.BLUE)
        self.lf.configure(bg=C.BG_S)
        self.cv.configure(bg=C.BG_S)
        self._inner.configure(bg=C.BG_S)
        self.sep.configure(bg=C.BORDER)
        self.btn_clear.configure(bg=C.BG_S, fg=C.ERR)
        self._render(self._sessions)
