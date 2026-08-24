"""
ui_visual_prototype.py — HELIOS Material Visual Design Target Prototype
========================================================================
Standalone high-end GUI prototype matching all 3 visual reference directions:
  1. Glassmorphism / Liquid Glass (translucent layered depth, top highlights)
  2. 3D Spatial Depth (atmospheric multi-zone ambient lighting)
  3. Soft Neumorphic & Skeuomorphic Controls (raised/inset depth, 3D buttons)

Supports modes for real desktop acceptance testing:
  --mode launch
  --mode hello
  --mode thinking
  --mode working
  --mode response
  --mode activity
  --mode all (default)
"""

from __future__ import annotations
import sys
import os
import argparse
import tkinter as tk

# ── COLOR PALETTE ────────────────────────────────────────────────────────────
BASE_BG        = "#080B18"   # Deep space floor
BASE_BG_ALT    = "#0D1224"   # Secondary panel dark
BASE_CARD      = "#111A36"   # Glass card fill

TEXT_PRIMARY   = "#F4F7FF"   # Pure bright white-blue
TEXT_SECONDARY = "#C7D0E0"   # Light blue-grey
TEXT_MUTED     = "#8994AA"   # Muted slate
TEXT_BLUE      = "#60A5FA"   # Electric blue
TEXT_CYAN      = "#38BDF8"   # Electric cyan
TEXT_VIOLET    = "#A78BFA"   # Electric violet
TEXT_EMERALD   = "#34D399"   # Emerald green
TEXT_AMBER     = "#FBBF24"   # Amber yellow

GLASS_BG       = "#0F1736"   # Translucent glass fill
GLASS_BG_HOVER = "#152048"   # Glass fill on hover
GLASS_BG_USER  = "#171B3E"   # User bubble glass fill
GLASS_BORDER   = "#233366"   # 1px glass border
GLASS_HIGHLIGHT= "#35456F"   # 1px glass top specular highlight stroke
GLASS_SHADOW   = "#03050D"   # Glass drop shadow

NEU_RAISED_BG  = "#131C3E"   # Raised button surface
NEU_PRESSED_BG = "#0A0F24"   # Pressed inset surface
NEU_LIGHT_SH   = "#2A3A74"   # Top-left light shadow edge
NEU_DARK_SH    = "#040612"   # Bottom-right dark shadow edge

SKEUO_BLUE_TOP = "#3B82F6"
SKEUO_BLUE_BOT = "#1D4ED8"
SKEUO_BLUE_SH  = "#1E3A8A"

SKEUO_EMERALD_TOP = "#10B981"
SKEUO_EMERALD_BOT = "#059669"


class HeliosVisualPrototype:
    """Standalone HELIOS Material Glass & Neumorphic Desktop Interface."""

    def __init__(self, mode: str = "all") -> None:
        self.mode = mode
        self.root = tk.Tk()
        self.root.title(f"HELIOS — Visual Target Prototype ({mode.upper()})")
        self.root.geometry("480x800")
        self.root.configure(bg=BASE_BG)
        self.root.overrideredirect(True)   # Frameless glass desktop window
        self.root.attributes("-topmost", True)

        # Center on screen
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 480) // 2
        y = (sh - 800) // 2
        self.root.geometry(f"480x800+{x}+{y}")

        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()

    def _build_ui(self) -> None:
        # Background canvas — multi-zone ambient lighting
        self.canvas = tk.Canvas(self.root, bg=BASE_BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # Foreground layout window on top of canvas
        self.fg = tk.Frame(self.canvas, bg=BASE_BG)
        self.canvas.create_window((0, 0), window=self.fg, anchor="nw", tags="fg_win")

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig("fg_win", width=e.width, height=e.height))

        # 1. Header Bar
        self._build_header()

        # 2. Body (Nav Rail + Main Feed)
        self.body_frame = tk.Frame(self.fg, bg=BASE_BG)
        self.body_frame.pack(fill="both", expand=True)

        self._build_nav_rail()
        self._build_feed_area()

        # 3. Floating Command Dock
        self._build_input_dock()

        # 4. Status Bar Footer
        self._build_status_bar()

    def _draw_ambient_background(self, w: int, h: int) -> None:
        """Render multi-zone environmental ambient light falloffs on canvas."""
        c = self.canvas
        c.delete("ambient")

        c.create_rectangle(0, 0, w, h, fill=BASE_BG, outline="", tags="ambient")

        # Zone 1: Top-Left Violet Ambient Glow
        self._draw_glow_blob(c, cx=int(w*0.1), cy=int(h*0.15), rx=260, ry=200,
                             center_color="#4C1D95", edge_color=BASE_BG, steps=10)

        # Zone 2: Top-Right Blue Ambient Glow
        self._draw_glow_blob(c, cx=int(w*0.9), cy=int(h*0.20), rx=240, ry=220,
                             center_color="#1E3A8A", edge_color=BASE_BG, steps=10)

        # Zone 3: Middle-Left Cyan Glow
        self._draw_glow_blob(c, cx=int(w*0.05), cy=int(h*0.65), rx=220, ry=180,
                             center_color="#0891B2", edge_color=BASE_BG, steps=10)

        # Zone 4: Bottom-Right Pink/Rose Accent
        self._draw_glow_blob(c, cx=int(w*0.95), cy=int(h*0.85), rx=200, ry=200,
                             center_color="#831843", edge_color=BASE_BG, steps=10)

    def _draw_glow_blob(self, c: tk.Canvas, cx: int, cy: int, rx: int, ry: int,
                        center_color: str, edge_color: str, steps: int = 8) -> None:
        r0, g0, b0 = _parse_hex(center_color)
        r1, g1, b1 = _parse_hex(edge_color)

        for i in range(steps, 0, -1):
            t = (steps - i) / steps
            t = t * t * t
            r = int(r1 + (r0 - r1) * t)
            g = int(g1 + (g0 - g1) * t)
            b = int(b1 + (b0 - b1) * t)
            color = f"#{r:02x}{g:02x}{b:02x}"
            scale = i / steps
            c.create_oval(cx - rx * scale, cy - ry * scale,
                          cx + rx * scale, cy + ry * scale,
                          fill=color, outline="", tags="ambient")

    def _on_canvas_resize(self, e: tk.Event) -> None:
        if e.width > 10 and e.height > 10:
            self._draw_ambient_background(e.width, e.height)
            self.canvas.itemconfig("fg_win", width=e.width, height=e.height)

    # 1. HEADER
    def _build_header(self) -> None:
        hdr = tk.Frame(self.fg, bg="#0A0E22", height=60)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Frame(hdr, bg=GLASS_BORDER, height=1).pack(fill="x", side="bottom")

        # Avatar Emblem
        av_cv = tk.Canvas(hdr, width=44, height=44, bg="#0A0E22", highlightthickness=0)
        av_cv.pack(side="left", padx=(14, 10), pady=8)

        av_cv.create_oval(3, 3, 41, 41, fill="#03050F", outline="")                         # Shadow
        av_cv.create_oval(2, 2, 40, 40, fill="#121B40", outline="#3B82F6", width=1.5)        # Outer Glass Ring
        av_cv.create_oval(6, 6, 36, 36, fill="#1E3A8A", outline="#60A5FA", width=1)          # Inner Gradient
        av_cv.create_text(21, 21, text="H", font=("Segoe UI Variable Display", 13, "bold"), fill=TEXT_PRIMARY)

        # Title Block
        tb = tk.Frame(hdr, bg="#0A0E22")
        tb.pack(side="left", fill="y", pady=10)

        tr = tk.Frame(tb, bg="#0A0E22")
        tr.pack(anchor="w")

        tk.Label(tr, text="HELIOS", font=("Segoe UI Variable Display", 14, "bold"), bg="#0A0E22", fg=TEXT_PRIMARY).pack(side="left")
        tk.Label(tr, text="  LOCAL AI  ", font=("Segoe UI", 9, "bold"), bg="#102A45", fg=TEXT_CYAN, padx=4, pady=1).pack(side="left", padx=(8, 0))

        sr = tk.Frame(tb, bg="#0A0E22")
        sr.pack(anchor="w", pady=(2, 0))

        tk.Label(sr, text="●", font=("Segoe UI", 8), bg="#0A0E22", fg=TEXT_EMERALD).pack(side="left", padx=(0, 4))
        tk.Label(sr, text="Gemma 3 4B · Privacy Guard Active", font=("Segoe UI", 9), bg="#0A0E22", fg=TEXT_MUTED).pack(side="left")

        # Controls
        ctrl = tk.Frame(hdr, bg="#0A0E22")
        ctrl.pack(side="right", padx=12)

        self._is_compact = False
        self._make_compact_toggle_btn(ctrl).pack(side="left", padx=(0, 6))

        self._win_btn(ctrl, "—", self.root.iconify)
        self._win_btn(ctrl, "□", lambda: None)
        self._win_btn(ctrl, "✕", self.root.destroy, is_close=True)

        for w in (hdr, tb, tr, sr):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._do_drag)

    def _make_compact_toggle_btn(self, parent: tk.Widget) -> tk.Widget:
        cv = tk.Canvas(parent, width=28, height=28, bg="#0A0E22", highlightthickness=0, cursor="hand2")

        def _draw(state="normal"):
            cv.delete("all")
            bg_c = "#152048" if state == "hover" else ("#0F1736" if state == "normal" else "#0A0F24")
            fg_c = TEXT_CYAN if (state == "hover" or self._is_compact) else TEXT_PRIMARY
            border_c = "#38BDF8" if self._is_compact else "#233366"
            icon_str = "↗" if self._is_compact else "▣"

            cv.create_oval(1, 1, 27, 27, fill="#03050D", outline="")
            cv.create_oval(2, 2, 26, 26, fill=bg_c, outline=border_c, width=1)
            if state != "pressed":
                cv.create_arc(3, 3, 25, 25, start=45, extent=180, style="arc", outline="#35456F", width=1)
            cv.create_text(14, 14, text=icon_str, font=("Segoe UI", 11, "bold"), fill=fg_c)

        _draw("normal")

        def _click(e):
            _draw("pressed")
            self._toggle_compact_mode()

        cv.bind("<Enter>", lambda e: _draw("hover"))
        cv.bind("<Leave>", lambda e: _draw("normal"))
        cv.bind("<Button-1>", lambda e: _draw("pressed"))
        cv.bind("<ButtonRelease-1>", _click)

        self._draw_compact_btn = _draw
        return cv

    def _toggle_compact_mode(self) -> None:
        if not self._is_compact:
            self._prev_geom = {
                "w": self.root.winfo_width(),
                "h": self.root.winfo_height(),
                "x": self.root.winfo_x(),
                "y": self.root.winfo_y()
            }
            self._is_compact = True
            if hasattr(self, "rail_frame"):
                self.rail_frame.pack_forget()
            new_x = max(0, self._prev_geom["x"])
            new_y = max(0, self._prev_geom["y"])
            self.root.geometry(f"420x760+{new_x}+{new_y}")
        else:
            self._is_compact = False
            if hasattr(self, "rail_frame"):
                self.rail_frame.pack(side="left", fill="y", before=self.feed_container)
            pw = getattr(self, "_prev_geom", {}).get("w", 480)
            ph = getattr(self, "_prev_geom", {}).get("h", 800)
            px = getattr(self, "_prev_geom", {}).get("x", 100)
            py = getattr(self, "_prev_geom", {}).get("y", 100)
            self.root.geometry(f"{pw}x{ph}+{px}+{py}")

        if hasattr(self, "_draw_compact_btn"):
            self._draw_compact_btn("normal")

    def _win_btn(self, parent: tk.Widget, text: str, cmd: callable, is_close: bool = False) -> None:
        btn = tk.Label(parent, text=text, font=("Segoe UI", 11), bg="#0A0E22", fg=TEXT_MUTED, width=3, cursor="hand2")
        btn.pack(side="left", padx=1)

        def _enter(e): btn.configure(bg="#DC2626" if is_close else "#1E2954", fg="#FFFFFF" if is_close else TEXT_PRIMARY)
        def _leave(e): btn.configure(bg="#0A0E22", fg=TEXT_MUTED)

        btn.bind("<Enter>", _enter)
        btn.bind("<Leave>", _leave)
        btn.bind("<ButtonRelease-1>", lambda e: cmd())

    # 2. NAVIGATION RAIL
    def _build_nav_rail(self) -> None:
        rail = tk.Frame(self.body_frame, bg="#0A0F24", width=56)
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)
        self.rail_frame = rail

        tk.Frame(rail, bg=GLASS_BORDER, width=1).pack(side="right", fill="y")

        is_act = (self.mode == "activity")
        nav_items = [
            ("chat",        "💬", "Chat", not is_act),
            ("history",     "📜", "History", False),
            ("desktop",     "💻", "Desktop", False),
            ("diagnostics", "📊", "Activity", is_act),
            ("settings",    "⚙", "Settings", False),
        ]

        for key, icon, label, active in nav_items:
            self._make_neu_nav_button(rail, icon, label, active)

    def _make_neu_nav_button(self, parent: tk.Widget, icon: str, label: str, active: bool) -> None:
        cv = tk.Canvas(parent, width=40, height=40, bg="#0A0F24", highlightthickness=0, cursor="hand2")
        cv.pack(pady=8, padx=8)

        def _draw(state="normal"):
            cv.delete("all")
            pad = 2
            if active or state == "active":
                bg_color = "#1D3A8A"
                fg_color = TEXT_CYAN
                border_c = "#38BDF8"
            elif state == "pressed":
                bg_color = NEU_PRESSED_BG
                fg_color = TEXT_SECONDARY
                border_c = NEU_DARK_SH
            elif state == "hover":
                bg_color = GLASS_BG_HOVER
                fg_color = TEXT_PRIMARY
                border_c = GLASS_HIGHLIGHT
            else:
                bg_color = NEU_RAISED_BG
                fg_color = TEXT_MUTED
                border_c = GLASS_BORDER

            cv.create_oval(pad, pad, 40-pad, 40-pad, fill=GLASS_SHADOW, outline="")
            cv.create_oval(pad+1, pad+1, 39-pad, 39-pad, fill=bg_color, outline=border_c, width=1)

            if state != "pressed":
                cv.create_arc(pad+2, pad+2, 38-pad, 38-pad, start=45, extent=180, style="arc", outline=NEU_LIGHT_SH, width=1)

            cv.create_text(20, 20, text=icon, font=("Segoe UI", 12), fill=fg_color)
            if active:
                cv.create_oval(18, 33, 22, 37, fill=TEXT_CYAN, outline="")

        _draw("normal")
        cv.bind("<Enter>", lambda e: _draw("hover"))
        cv.bind("<Leave>", lambda e: _draw("normal"))
        cv.bind("<Button-1>", lambda e: _draw("pressed"))
        cv.bind("<ButtonRelease-1>", lambda e: _draw("hover"))

    # 3. FEED AREA
    def _build_feed_area(self) -> None:
        fc = tk.Frame(self.body_frame, bg=BASE_BG)
        fc.pack(side="left", fill="both", expand=True)
        self.feed_container = fc

        self.feed_cv = tk.Canvas(fc, bg=BASE_BG, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(fc, orient="vertical", command=self.feed_cv.yview)
        self.feed_cv.configure(yscrollcommand=vsb.set)

        self.feed_cv.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.feed_inner = tk.Frame(self.feed_cv, bg=BASE_BG)
        self.feed_win = self.feed_cv.create_window((0, 0), window=self.feed_inner, anchor="nw")

        self.feed_inner.bind("<Configure>", lambda e: self.feed_cv.configure(scrollregion=self.feed_cv.bbox("all")))
        self.feed_cv.bind("<Configure>", lambda e: self.feed_cv.itemconfig(self.feed_win, width=e.width))

        self.feed_cv.bind_all("<MouseWheel>", lambda e: self.feed_cv.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._render_feed_mode()

    def _render_feed_mode(self) -> None:
        m = self.mode
        pad = 12

        # A. LAUNCH / WELCOME LANDING STATE
        if m in ("launch", "all"):
            w_box = self._create_glass_card(self.feed_inner, accent_color=TEXT_CYAN)
            w_box.pack(fill="x", padx=pad, pady=(14, 8))

            w_hdr = tk.Frame(w_box.body, bg=w_box.bg)
            w_hdr.pack(anchor="w")

            tk.Label(w_hdr, text="◉  HELIOS", font=("Segoe UI Variable Display", 16, "bold"), bg=w_box.bg, fg=TEXT_PRIMARY).pack(side="left")
            tk.Label(w_box.body, text="Autonomous Desktop AI Agent · Local First", font=("Segoe UI", 10), bg=w_box.bg, fg=TEXT_MUTED).pack(anchor="w", pady=(2, 10))

            grid = tk.Frame(w_box.body, bg=w_box.bg)
            grid.pack(fill="x", pady=4)
            grid.columnconfigure(0, weight=1)
            grid.columnconfigure(1, weight=1)

            actions = [
                ("✍ Write & Create", "Draft, edit, compose", TEXT_BLUE),
                ("💡 Analyze & Explain", "Code, documents, logs", TEXT_CYAN),
                ("🌐 Search the Web", "Real-time web research", TEXT_VIOLET),
                ("📅 Plan & Task", "Automate desktop actions", TEXT_EMERALD),
            ]
            for idx, (title, desc, color) in enumerate(actions):
                r, c = divmod(idx, 2)
                card_item = tk.Frame(grid, bg="#131C40", highlightthickness=1, highlightbackground=GLASS_BORDER, cursor="hand2")
                card_item.grid(row=r, column=c, padx=4, pady=4, sticky="ew")

                cb = tk.Frame(card_item, bg="#131C40", padx=10, pady=8)
                cb.pack(fill="both", expand=True)

                tk.Label(cb, text=title, font=("Segoe UI", 10, "bold"), bg="#131C40", fg=color).pack(anchor="w")
                tk.Label(cb, text=desc, font=("Segoe UI", 8), bg="#131C40", fg=TEXT_MUTED).pack(anchor="w")

        # B. USER MESSAGE CARD (Right-aligned 3-layer glass)
        if m in ("hello", "thinking", "working", "response", "all"):
            u_outer = tk.Frame(self.feed_inner, bg=BASE_BG)
            u_outer.pack(fill="x", padx=pad, pady=8)

            u_card = tk.Frame(u_outer, bg=GLASS_BG_USER, highlightthickness=1, highlightbackground="#3B82F6")
            u_card.pack(anchor="e")

            tk.Frame(u_card, bg="#60A5FA", height=1).pack(fill="x")

            u_body = tk.Frame(u_card, bg=GLASS_BG_USER, padx=14, pady=10)
            u_body.pack()

            u_text = "hello" if m == "hello" else "Find the best Logitech mechanical keyboard on Amazon and compare prices."
            tk.Label(u_body, text="You", font=("Segoe UI", 9, "bold"), bg=GLASS_BG_USER, fg=TEXT_BLUE).pack(anchor="w")
            tk.Label(u_body, text=u_text, font=("Segoe UI", 11), bg=GLASS_BG_USER, fg=TEXT_PRIMARY, wraplength=320, justify="left").pack(anchor="w", pady=(4, 0))

        # C. THINKING STATE CARD
        if m in ("thinking", "all"):
            t_card = self._create_glass_card(self.feed_inner, accent_color=TEXT_VIOLET)
            t_card.pack(fill="x", padx=pad, pady=6)

            t_hdr = tk.Frame(t_card.body, bg=t_card.bg)
            t_hdr.pack(fill="x")
            tk.Label(t_hdr, text="◉  THINKING", font=("Segoe UI", 10, "bold"), bg=t_card.bg, fg=TEXT_VIOLET).pack(side="left")
            tk.Label(t_hdr, text="Analyzing user request & intent...", font=("Segoe UI", 9), bg=t_card.bg, fg=TEXT_MUTED).pack(side="left", padx=8)

        # D. WORKING STATE CARD
        if m in ("working", "all"):
            w_card = self._create_glass_card(self.feed_inner, accent_color=TEXT_CYAN)
            w_card.pack(fill="x", padx=pad, pady=6)

            w_row = tk.Frame(w_card.body, bg=w_card.bg)
            w_row.pack(fill="x")
            tk.Label(w_row, text="◉  WORKING", font=("Segoe UI", 10, "bold"), bg=w_card.bg, fg=TEXT_CYAN).pack(side="left")
            tk.Label(w_row, text="Opening Chrome browser → Amazon.com", font=("Segoe UI", 10), bg=w_card.bg, fg=TEXT_PRIMARY).pack(side="left", padx=8)

        # E. HELIOS RESPONSE + COMMERCE PRODUCT CARD
        if m in ("response", "all"):
            h_card = self._create_glass_card(self.feed_inner, accent_color=TEXT_BLUE)
            h_card.pack(fill="x", padx=pad, pady=8)

            h_hdr = tk.Frame(h_card.body, bg=h_card.bg)
            h_hdr.pack(fill="x")

            tk.Label(h_hdr, text="H  HELIOS", font=("Segoe UI Variable Display", 11, "bold"), bg=h_card.bg, fg=TEXT_PRIMARY).pack(side="left")
            tk.Label(h_hdr, text="  Gemma 3 4B  ", font=("Segoe UI", 8), bg="#1E295B", fg=TEXT_CYAN, padx=4).pack(side="left", padx=8)
            tk.Label(h_hdr, text="02:31 PM", font=("Segoe UI", 9), bg=h_card.bg, fg=TEXT_MUTED).pack(side="right")

            msg_body = ("I found 3 verified Logitech mechanical keyboards matching your request on Amazon India. "
                        "Below is the top recommended offer:")
            tk.Label(h_card.body, text=msg_body, font=("Segoe UI", 11), bg=h_card.bg, fg=TEXT_PRIMARY, wraplength=380, justify="left").pack(anchor="w", pady=(8, 10))

            # Product Tile
            p_card = self._create_glass_card(h_card.body, accent_color=TEXT_CYAN)
            p_card.pack(fill="x", pady=4)

            p_tag = tk.Frame(p_card.body, bg=p_card.bg)
            p_tag.pack(anchor="w")
            tk.Label(p_tag, text="  PRODUCT OFFER  ", font=("Segoe UI", 8, "bold"), bg="#172554", fg=TEXT_CYAN, padx=4, pady=1).pack(side="left")
            tk.Label(p_tag, text="  ✓ VERIFIED  ", font=("Segoe UI", 8, "bold"), bg="#064E3B", fg=TEXT_EMERALD, padx=4, pady=1).pack(side="left", padx=6)

            tk.Label(p_card.body, text="Logitech MX Mechanical Wireless Keyboard", font=("Segoe UI Variable Display", 12, "bold"), bg=p_card.bg, fg=TEXT_PRIMARY).pack(anchor="w", pady=(6, 2))

            p_row = tk.Frame(p_card.body, bg=p_card.bg)
            p_row.pack(fill="x", pady=(4, 8))

            tk.Label(p_row, text="₹13,995", font=("Segoe UI", 16, "bold"), bg=p_card.bg, fg=TEXT_CYAN).pack(side="left")
            tk.Label(p_row, text="  ★ 4.8 (1,240 ratings)  ·  Amazon.in", font=("Segoe UI", 9), bg=p_card.bg, fg=TEXT_MUTED).pack(side="left", padx=6)

            btn_row = tk.Frame(p_card.body, bg=p_card.bg)
            btn_row.pack(fill="x", pady=(4, 2))

            self._make_skeuomorphic_button(btn_row, text="View Details", color_scheme="blue").pack(side="left", padx=(0, 8))
            self._make_skeuomorphic_button(btn_row, text="🛒 Add to Cart", color_scheme="emerald").pack(side="left")

        # F. ACTIVITY / STATISTICS SECTION (Reference C style)
        if m in ("activity", "all"):
            s_sec = tk.Frame(self.feed_inner, bg=BASE_BG)
            s_sec.pack(fill="x", padx=pad, pady=(16, 8))

            tk.Label(s_sec, text="SESSION ACTIVITY & TELEMETRY", font=("Segoe UI", 9, "bold"), bg=BASE_BG, fg=TEXT_MUTED).pack(anchor="w", pady=(0, 6))

            s_grid = tk.Frame(s_sec, bg=BASE_BG)
            s_grid.pack(fill="x")
            s_grid.columnconfigure(0, weight=1)
            s_grid.columnconfigure(1, weight=1)

            # Card 1: Session Actions
            c1 = self._create_glass_card(s_grid)
            c1.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
            tk.Label(c1.body, text="SESSION ACTIONS", font=("Segoe UI", 8, "bold"), bg=c1.bg, fg=TEXT_MUTED).pack(anchor="w")
            tk.Label(c1.body, text="12", font=("Segoe UI Variable Display", 22, "bold"), bg=c1.bg, fg=TEXT_PRIMARY).pack(anchor="w")
            tk.Label(c1.body, text="✓ 98% Verified", font=("Segoe UI", 9), bg=c1.bg, fg=TEXT_EMERALD).pack(anchor="w")

            # Card 2: LLM Latency
            c2 = self._create_glass_card(s_grid)
            c2.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
            tk.Label(c2.body, text="LLM LATENCY", font=("Segoe UI", 8, "bold"), bg=c2.bg, fg=TEXT_MUTED).pack(anchor="w")
            tk.Label(c2.body, text="42ms", font=("Segoe UI Variable Display", 22, "bold"), bg=c2.bg, fg=TEXT_CYAN).pack(anchor="w")
            tk.Label(c2.body, text="● Local Gemma 3", font=("Segoe UI", 9), bg=c2.bg, fg=TEXT_MUTED).pack(anchor="w")

            # Card 3: Desktop Target
            c3 = self._create_glass_card(s_grid)
            c3.grid(row=1, column=0, padx=3, pady=3, sticky="ew")
            tk.Label(c3.body, text="ACTIVE APP", font=("Segoe UI", 8, "bold"), bg=c3.bg, fg=TEXT_MUTED).pack(anchor="w")
            tk.Label(c3.body, text="Chrome", font=("Segoe UI Variable Display", 18, "bold"), bg=c3.bg, fg=TEXT_PRIMARY).pack(anchor="w")
            tk.Label(c3.body, text="● Foreground Focused", font=("Segoe UI", 9), bg=c3.bg, fg=TEXT_BLUE).pack(anchor="w")

            # Card 4: Privacy Guard
            c4 = self._create_glass_card(s_grid)
            c4.grid(row=1, column=1, padx=3, pady=3, sticky="ew")
            tk.Label(c4.body, text="SECURITY", font=("Segoe UI", 8, "bold"), bg=c4.bg, fg=TEXT_MUTED).pack(anchor="w")
            tk.Label(c4.body, text="Protected", font=("Segoe UI Variable Display", 18, "bold"), bg=c4.bg, fg=TEXT_EMERALD).pack(anchor="w")
            tk.Label(c4.body, text="● 100% Offline Mode", font=("Segoe UI", 9), bg=c4.bg, fg=TEXT_EMERALD).pack(anchor="w")

    def _create_glass_card(self, parent: tk.Widget, accent_color: str = None):
        class _GlassCardWrapper: pass
        res = _GlassCardWrapper()
        res.shadow = tk.Frame(parent, bg=GLASS_SHADOW)

        res.card = tk.Frame(res.shadow, bg=GLASS_BG, highlightthickness=1, highlightbackground=GLASS_BORDER)
        res.card.pack(fill="both", expand=True, padx=(0, 1), pady=(0, 1))

        res.hl = tk.Frame(res.card, bg=GLASS_HIGHLIGHT, height=1)
        res.hl.pack(fill="x")

        res.row = tk.Frame(res.card, bg=GLASS_BG)
        res.row.pack(fill="both", expand=True)

        if accent_color:
            res.accent = tk.Frame(res.row, bg=accent_color, width=3)
            res.accent.pack(side="left", fill="y")

        res.bg = GLASS_BG
        res.body = tk.Frame(res.row, bg=GLASS_BG, padx=12, pady=10)
        res.body.pack(fill="both", expand=True)

        res.pack = res.shadow.pack
        res.grid = res.shadow.grid
        return res

    def _make_skeuomorphic_button(self, parent: tk.Widget, text: str, color_scheme: str = "blue", cmd: callable = None) -> tk.Widget:
        if color_scheme == "emerald":
            top_c, bot_c, sh_c = SKEUO_EMERALD_TOP, SKEUO_EMERALD_BOT, "#047857"
        else:
            top_c, bot_c, sh_c = SKEUO_BLUE_TOP, SKEUO_BLUE_BOT, SKEUO_BLUE_SH

        btn_frame = tk.Frame(parent, bg=sh_c, bd=0, cursor="hand2")
        inner = tk.Frame(btn_frame, bg=bot_c, highlightthickness=1, highlightbackground=top_c)
        inner.pack(fill="both", expand=True, padx=(0, 1), pady=(0, 1.5))

        lbl = tk.Label(inner, text=text, font=("Segoe UI", 9, "bold"), bg=bot_c, fg="#FFFFFF", padx=12, pady=5)
        lbl.pack()

        def _press(e): inner.pack_configure(padx=(1, 0), pady=(1.5, 0))
        def _release(e):
            inner.pack_configure(padx=(0, 1), pady=(0, 1.5))
            if cmd: cmd()

        for w in (btn_frame, inner, lbl):
            w.bind("<Button-1>", _press)
            w.bind("<ButtonRelease-1>", _release)

        return btn_frame

    # 4. INPUT DOCK
    def _build_input_dock(self) -> None:
        dock_outer = tk.Frame(self.fg, bg="#0A0F24")
        dock_outer.pack(fill="x", side="top", padx=14, pady=(4, 6))

        dock = tk.Frame(dock_outer, bg="#0F1738", highlightthickness=1, highlightbackground="#2E4288")
        dock.pack(fill="x")

        tk.Frame(dock, bg="#4A65BD", height=1).pack(fill="x")

        row = tk.Frame(dock, bg="#0F1738", padx=8, pady=6)
        row.pack(fill="x")

        self._make_mini_tool_btn(row, "+", TEXT_CYAN)
        self._make_mini_tool_btn(row, "📷", TEXT_VIOLET)

        entry = tk.Entry(row, font=("Segoe UI", 11), bg="#0B1028", fg=TEXT_PRIMARY, insertbackground=TEXT_CYAN, relief="flat", bd=0)
        entry.insert(0, "Write a command or ask HELIOS...")
        entry.pack(side="left", fill="x", expand=True, padx=8)

        self._make_mini_tool_btn(row, "🎤", TEXT_AMBER)
        send_btn = self._make_skeuomorphic_button(row, text="➤", color_scheme="blue", cmd=lambda: None)
        send_btn.pack(side="left", padx=(4, 0))

    def _make_mini_tool_btn(self, parent: tk.Widget, char: str, fg_color: str) -> None:
        cv = tk.Canvas(parent, width=32, height=32, bg="#0F1738", highlightthickness=0, cursor="hand2")
        cv.pack(side="left", padx=2)
        cv.create_oval(2, 2, 30, 30, fill="#141E47", outline=GLASS_BORDER)
        cv.create_text(16, 16, text=char, font=("Segoe UI", 11, "bold"), fill=fg_color)

    # 5. STATUS BAR FOOTER
    def _build_status_bar(self) -> None:
        sb = tk.Frame(self.fg, bg="#060914", height=24)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)

        tk.Frame(sb, bg=GLASS_BORDER, height=1).pack(fill="x", side="top")

        tk.Label(sb, text="  ● READY", font=("Segoe UI", 8, "bold"), bg="#060914", fg=TEXT_EMERALD).pack(side="left")
        tk.Label(sb, text="  |  Privacy Guard Active  ·  Offline Mode", font=("Segoe UI", 8), bg="#060914", fg=TEXT_MUTED).pack(side="left")
        tk.Label(sb, text="HELIOS v4.0  ", font=("Segoe UI", 8), bg="#060914", fg=TEXT_MUTED).pack(side="right")

    def _start_drag(self, e: tk.Event) -> None:
        self._drag_x = e.x
        self._drag_y = e.y

    def _do_drag(self, e: tk.Event) -> None:
        dx = e.x - self._drag_x
        dy = e.y - self._drag_y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def run(self) -> None:
        self.root.mainloop()


def _parse_hex(c: str) -> tuple[int, int, int]:
    try: return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
    except Exception: return 8, 11, 24


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="all", choices=["launch", "hello", "thinking", "working", "response", "activity", "all"])
    args = parser.parse_args()

    app = HeliosVisualPrototype(mode=args.mode)
    app.run()
