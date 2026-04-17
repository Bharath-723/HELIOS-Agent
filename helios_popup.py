"""
HELIOS - Desktop Chat Popup
Floating chat window with model switcher, history panel, selectable text
Run: python helios_popup.py
"""

import tkinter as tk
import threading
import queue
from datetime import datetime

# ── Colors ────────────────────────────────────────────────────────────────
C = {
    "header":  "#4f46e5",
    "chat_bg": "#f0f2f5",
    "user_bg": "#4f46e5",
    "bot_bg":  "#ffffff",
    "input_bg":"#ffffff",
    "hist_bg": "#1e1e2e",
    "hist_hdr":"#2a2a3e",
    "border":  "#e5e7eb",
    "send":    "#4f46e5",
    "fg_hdr":  "#ffffff",
    "fg_sub":  "#c7d2fe",
    "fg_user": "#ffffff",
    "fg_bot":  "#111827",
    "fg_time": "#9ca3af",
    "fg_dim":  "#888899",
    "fg_hist": "#e0e0f0",
    "accent":  "#6366f1",
}
F = lambda s, b="normal": ("Segoe UI", s, b)


class HELIOSPopup:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HELIOS")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.97)
        self.root.configure(bg=C["chat_bg"])

        W, H = 370, 540
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{sw-W-20}+{sh-H-60}")
        self.root.resizable(False, False)

        self.agent    = None
        self.q        = queue.Queue()
        self._dx = self._dy = 0
        self._dragging = False
        self._drag_sx = self._drag_sy = 0
        self._is_ph   = True
        self._anim_id = None
        self.t_row    = None
        self.hist_win = None

        self._build()
        self._load_agent()
        self._poll()

    # ── BUILD ─────────────────────────────────────────────────────────────
    def _build(self):
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Header
        hdr = tk.Frame(self.root, bg=C["header"], height=62)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)
        hdr.grid_propagate(False)

        av = tk.Canvas(hdr, width=38, height=38, bg=C["header"], highlightthickness=0)
        av.grid(row=0, column=0, padx=(10,8), pady=12)
        av.create_oval(1,1,37,37, fill=C["accent"], outline="#818cf8")
        av.create_text(19, 19, text="🌞", font=("Segoe UI Emoji", 14))

        tf = tk.Frame(hdr, bg=C["header"])
        tf.grid(row=0, column=1, sticky="w")
        tk.Label(tf, text="HELIOS", font=F(12,"bold"),
                 bg=C["header"], fg=C["fg_hdr"]).pack(anchor="w")
        self.status_lbl = tk.Label(tf, text="Initializing...",
                                   font=F(8), bg=C["header"], fg=C["fg_sub"])
        self.status_lbl.pack(anchor="w")

        bf = tk.Frame(hdr, bg=C["header"])
        bf.grid(row=0, column=2, padx=8)

        self.dots_btn = tk.Label(bf, text="⋮", font=F(16), bg=C["header"],
                                  fg=C["fg_sub"], cursor="hand2")
        self.dots_btn.pack(side="left", padx=(0,8))
        self.dots_btn.bind("<ButtonRelease-1>", self._on_dots_click)

        self.close_btn = tk.Label(bf, text="✕", font=F(13), bg=C["header"],
                                   fg=C["fg_sub"], cursor="hand2")
        self.close_btn.pack(side="left")
        self.close_btn.bind("<ButtonRelease-1>", self._on_close_click)

        for w in [hdr, av, tf]:
            w.bind("<ButtonPress-1>",   self._drag_start)
            w.bind("<B1-Motion>",       self._drag_do)
            w.bind("<ButtonRelease-1>", self._drag_end)

        # Chat canvas
        cf = tk.Frame(self.root, bg=C["chat_bg"])
        cf.grid(row=1, column=0, sticky="nsew")
        cf.rowconfigure(0, weight=1)
        cf.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(cf, bg=C["chat_bg"], highlightthickness=0, bd=0)
        sb = tk.Scrollbar(cf, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        self.msgs = tk.Frame(self.canvas, bg=C["chat_bg"])
        self._cw = self.canvas.create_window((0,0), window=self.msgs, anchor="nw")
        self.msgs.bind("<Configure>", lambda e:
            self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e:
            self.canvas.itemconfig(self._cw, width=e.width))
        self.canvas.bind_all("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Divider
        tk.Frame(self.root, bg=C["border"], height=1).grid(row=2, column=0, sticky="ew")

        # Input bar
        inp = tk.Frame(self.root, bg=C["input_bg"])
        inp.grid(row=3, column=0, sticky="ew")
        inp.columnconfigure(1, weight=1)

        tk.Label(inp, text="📎", font=F(13), bg=C["input_bg"],
                 fg="#9ca3af").grid(row=0, column=0, padx=(10,6), pady=10)

        self.entry = tk.Entry(inp, font=F(10), bg=C["input_bg"], fg="#9ca3af",
                              relief="flat", bd=0, insertbackground=C["send"])
        self.entry.grid(row=0, column=1, sticky="ew", pady=12)
        self.entry.insert(0, "Write a message...")
        self.entry.bind("<FocusIn>",  self._ph_clear)
        self.entry.bind("<FocusOut>", self._ph_restore)
        self.entry.bind("<Return>",   self._send)

        tk.Label(inp, text="🙂", font=F(13), bg=C["input_bg"],
                 fg="#9ca3af").grid(row=0, column=2, padx=4)

        sc = tk.Canvas(inp, width=36, height=36, bg=C["input_bg"],
                       highlightthickness=0, cursor="hand2")
        sc.grid(row=0, column=3, padx=(4,10), pady=8)
        sc.create_oval(2,2,34,34, fill=C["send"], outline="")
        sc.create_text(18,18, text="➤", font=F(11,"bold"), fill="white")
        sc.bind("<Button-1>", self._send)

        # Welcome
        self._add_msg("Hi! 👋 I'm HELIOS — your desktop AI.\nAsk me anything in your own words.", "helios")

    # ── DRAG ──────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._dragging = False
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()
        self._drag_sx = e.x_root
        self._drag_sy = e.y_root
    def _drag_do(self, e):
        if abs(e.x_root-self._drag_sx)>3 or abs(e.y_root-self._drag_sy)>3:
            self._dragging = True
        if self._dragging:
            self.root.geometry(f"+{e.x_root-self._dx}+{e.y_root-self._dy}")
    def _drag_end(self, e):
        self.root.after(50, lambda: setattr(self, '_dragging', False))
    def _on_dots_click(self, e):
        if not self._dragging: self._toggle_hist()
    def _on_close_click(self, e):
        if not self._dragging:
            if self.agent:
                try: self.agent.shutdown()
                except: pass
            self.root.destroy()

    # ── PLACEHOLDER ───────────────────────────────────────────────────────
    def _ph_clear(self, e):
        if self._is_ph:
            self.entry.delete(0, tk.END)
            self.entry.configure(fg="#374151")
            self._is_ph = False
    def _ph_restore(self, e):
        if not self.entry.get():
            self.entry.insert(0, "Write a message...")
            self.entry.configure(fg="#9ca3af")
            self._is_ph = True

    # ── MESSAGES (tk.Text for selectability) ─────────────────────────────
    def _add_msg(self, text: str, sender: str):
        ts = datetime.now().strftime("%I:%M %p")
        is_user = sender == "user"

        row = tk.Frame(self.msgs, bg=C["chat_bg"])
        row.pack(fill="x", padx=10, pady=(6,0))

        # Calculate height
        lines = sum(max(1, -(-len(p)//34)) for p in text.split("\n"))
        lines = max(1, min(lines, 25))

        txt = tk.Text(row, font=F(10),
                      bg=C["user_bg"] if is_user else C["bot_bg"],
                      fg=C["fg_user"] if is_user else C["fg_bot"],
                      relief="flat", bd=0, padx=12, pady=8,
                      wrap="word", width=34, height=lines,
                      cursor="xterm", exportselection=True)
        txt.insert("1.0", text)
        txt.configure(state="disabled")

        # Right-click menu
        menu = tk.Menu(txt, tearoff=0)
        menu.add_command(label="Copy Selected",
                         command=lambda t=txt: self._copy_sel(t))
        menu.add_command(label="Copy All",
                         command=lambda t=txt: self._copy_all(t))
        txt.bind("<Button-3>", lambda e, m=menu: m.post(e.x_root, e.y_root))
        # Allow selection on click
        def enable_sel(e, t=txt):
            t.configure(state="normal")
            t.after(1, lambda: t.configure(state="disabled"))
        txt.bind("<Button-1>", enable_sel)

        if is_user:
            txt.pack(anchor="e")
        else:
            txt.configure(highlightthickness=1,
                          highlightbackground="#e5e7eb",
                          highlightcolor="#e5e7eb")
            txt.pack(anchor="w")

        tk.Label(row, text=ts, font=F(7), bg=C["chat_bg"],
                 fg=C["fg_time"]).pack(anchor="e" if is_user else "w", pady=(2,0))

        self.root.after(150, lambda: self.canvas.yview_moveto(1.0))

    def _copy_sel(self, t):
        try:
            s = t.get("sel.first", "sel.last")
            self.root.clipboard_clear(); self.root.clipboard_append(s)
        except tk.TclError: pass

    def _copy_all(self, t):
        self.root.clipboard_clear()
        self.root.clipboard_append(t.get("1.0", tk.END).strip())

    # ── TYPING INDICATOR ──────────────────────────────────────────────────
    def _show_typing(self):
        self.t_row = tk.Frame(self.msgs, bg=C["chat_bg"])
        self.t_row.pack(fill="x", padx=10, pady=(6,0))
        self._tlbl = tk.Label(self.t_row, text="●  ○  ○  thinking",
                              font=("Segoe UI", 9, "italic"),
                              bg=C["bot_bg"], fg="#6b7280", padx=10, pady=6)
        self._tlbl.pack(anchor="w")
        self._anim(0)
        self.root.after(150, lambda: self.canvas.yview_moveto(1.0))

    def _anim(self, n):
        fs = ["●  ○  ○","●  ●  ○","●  ●  ●","○  ●  ●","○  ○  ●"]
        if self.t_row and self.t_row.winfo_exists():
            self._tlbl.configure(text=f"{fs[n%5]}  thinking")
            self._anim_id = self.root.after(350, self._anim, n+1)

    def _hide_typing(self):
        if self._anim_id:
            self.root.after_cancel(self._anim_id); self._anim_id = None
        if self.t_row and self.t_row.winfo_exists():
            self.t_row.destroy(); self.t_row = None

    # ── SEND / RECEIVE ────────────────────────────────────────────────────
    def _send(self, e=None):
        txt = self.entry.get().strip()
        if not txt or self._is_ph or not self.agent: return
        self.entry.delete(0, tk.END); self._is_ph = False
        self._add_msg(txt, "user")
        self._show_typing()
        threading.Thread(target=self._bg, args=(txt,), daemon=True).start()

    def _bg(self, txt):
        try: resp = self.agent.process(txt)
        except Exception as ex: resp = f"Error: {ex}"
        self.q.put(resp)

    def _poll(self):
        try:
            while True:
                resp = self.q.get_nowait()
                self._hide_typing()
                self._add_msg(resp, "helios")
        except queue.Empty: pass
        self.root.after(100, self._poll)

    # ── HISTORY PANEL ─────────────────────────────────────────────────────
    def _toggle_hist(self, e=None):
        if self.hist_win and self.hist_win.winfo_exists():
            self.hist_win.destroy(); self.hist_win = None; return
        if not self.agent: return
        self._open_hist()

    def _open_hist(self):
        px, py = self.root.winfo_x(), self.root.winfo_y()
        self.hist_win = tk.Toplevel(self.root)
        self.hist_win.title("History")
        self.hist_win.overrideredirect(True)
        self.hist_win.attributes("-topmost", True)
        self.hist_win.geometry(f"270x520+{px-275}+{py}")
        self.hist_win.configure(bg=C["hist_bg"])

        # Header
        hdr = tk.Frame(self.hist_win, bg=C["hist_hdr"], height=50)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="  🕐 Chat History", font=F(11,"bold"),
                 bg=C["hist_hdr"], fg=C["fg_hist"]).pack(side="left", pady=14)
        cl = tk.Label(hdr, text="✕", font=F(12), bg=C["hist_hdr"],
                      fg=C["fg_dim"], cursor="hand2")
        cl.pack(side="right", padx=10)
        cl.bind("<Button-1>", lambda e: self.hist_win.destroy())

        # ── Model Switcher ───────────────────────────────────────────────
        msf = tk.Frame(self.hist_win, bg=C["hist_hdr"], pady=6)
        msf.pack(fill="x")
        tk.Label(msf, text="  🤖 Model:", font=F(9),
                 bg=C["hist_hdr"], fg=C["fg_dim"]).pack(side="left")

        self.model_var = tk.StringVar(value=self.agent.llm.ollama_model)
        available = self.agent.llm.get_available_models()
        if not available:
            available = [self.agent.llm.ollama_model]

        om = tk.OptionMenu(msf, self.model_var, *available,
                           command=self._switch_model)
        om.configure(font=F(8), bg="#333355", fg="#c0c0e0",
                     activebackground="#4444aa", relief="flat",
                     highlightthickness=0, width=16)
        om["menu"].configure(bg="#333355", fg="#c0c0e0", font=F(9))
        om.pack(side="left", padx=6)

        # Cloud provider toggle
        tk.Frame(self.hist_win, bg="#333344", height=1).pack(fill="x")
        cpf = tk.Frame(self.hist_win, bg=C["hist_hdr"], pady=4)
        cpf.pack(fill="x")
        tk.Label(cpf, text="  ☁ Cloud:", font=F(9),
                 bg=C["hist_hdr"], fg=C["fg_dim"]).pack(side="left")
        self.cloud_var = tk.StringVar(value=self.agent.llm.cloud_provider)
        for cp in ["gemini", "gpt"]:
            has_key = (self.agent.llm._has_gemini_key() if cp == "gemini"
                      else self.agent.llm._has_openai_key())
            label = f"{'✓' if has_key else '✗'} {cp}"
            rb = tk.Radiobutton(cpf, text=label, variable=self.cloud_var,
                                value=cp, command=lambda c=cp: self._switch_cloud(c),
                                font=F(8), bg=C["hist_hdr"],
                                fg="#22c55e" if has_key else "#ef4444",
                                selectcolor=C["hist_hdr"],
                                activebackground=C["hist_hdr"])
            rb.pack(side="left", padx=6)

        # Mode switcher
        tk.Frame(self.hist_win, bg="#333344", height=1).pack(fill="x")
        mdf = tk.Frame(self.hist_win, bg=C["hist_hdr"], pady=4)
        mdf.pack(fill="x")
        tk.Label(mdf, text="  ⚡ Mode:", font=F(9),
                 bg=C["hist_hdr"], fg=C["fg_dim"]).pack(side="left")
        self.mode_var = tk.StringVar(value=self.agent.llm.mode)
        for m in ["offline", "auto", "online"]:
            rb = tk.Radiobutton(mdf, text=m, variable=self.mode_var,
                                value=m, command=lambda mv=m: self._switch_mode(mv),
                                font=F(8), bg=C["hist_hdr"], fg=C["fg_hist"],
                                selectcolor=C["hist_hdr"], activebackground=C["hist_hdr"])
            rb.pack(side="left", padx=4)

        # New chat
        tk.Frame(self.hist_win, bg="#333344", height=1).pack(fill="x")
        nc = tk.Label(self.hist_win, text="  ＋  New Chat",
                      font=F(10), bg=C["accent"], fg="white",
                      cursor="hand2", pady=7)
        nc.pack(fill="x", padx=8, pady=6)
        nc.bind("<Button-1>", self._new_chat)

        # Sessions (scrollable)
        lf = tk.Frame(self.hist_win, bg=C["hist_bg"])
        lf.pack(fill="both", expand=True, padx=4)
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)
        cv = tk.Canvas(lf, bg=C["hist_bg"], highlightthickness=0)
        sb = tk.Scrollbar(lf, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=sb.set)
        cv.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        inner = tk.Frame(cv, bg=C["hist_bg"])
        win_id = cv.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(win_id, width=e.width))
        cv.bind("<MouseWheel>", lambda e: cv.yview_scroll(int(-1*(e.delta/120)),"units"))

        sessions = self.agent.history.get_all()
        if not sessions:
            tk.Label(inner, text="No history yet.", font=F(9),
                     bg=C["hist_bg"], fg="#555577", pady=20).pack()
        else:
            for s in sessions:
                self._hist_item(inner, s)

        # Clear all
        tk.Frame(self.hist_win, bg="#333344", height=1).pack(fill="x")
        clr = tk.Label(self.hist_win, text="🗑  Clear All History",
                       font=F(9), bg=C["hist_bg"], fg="#ff6b6b",
                       cursor="hand2", pady=7)
        clr.pack()
        clr.bind("<Button-1>", self._clear_hist)

    def _hist_item(self, parent, session: dict):
        sid   = session["id"]
        title = session.get("title", sid)
        ts    = session.get("started","")[:16].replace("T"," ")
        count = session.get("message_count", 0)

        item = tk.Frame(parent, bg=C["hist_hdr"], cursor="hand2")
        item.pack(fill="x", padx=6, pady=3)
        tk.Label(item, text=title, font=F(9,"bold"), bg=C["hist_hdr"],
                 fg=C["fg_hist"], wraplength=220, justify="left").pack(
            anchor="w", padx=8, pady=(6,1))
        tk.Label(item, text=f"{ts}  ·  {count} msgs", font=F(7),
                 bg=C["hist_hdr"], fg="#555577").pack(anchor="w", padx=8, pady=(0,6))

        def on_enter(e): item.configure(bg="#333366")
        def on_leave(e): item.configure(bg=C["hist_hdr"])
        def on_click(e, s=sid): self._load_sess(s)
        item.bind("<Enter>", on_enter); item.bind("<Leave>", on_leave)
        item.bind("<Button-1>", on_click)
        for child in item.winfo_children():
            child.bind("<Enter>", on_enter); child.bind("<Leave>", on_leave)
            child.bind("<Button-1>", on_click)

    def _load_sess(self, sid: str):
        if not self.agent: return
        msgs = self.agent.history.load(sid)
        for w in self.msgs.winfo_children(): w.destroy()
        for m in msgs: self._add_msg(m["content"], m["role"])
        if self.hist_win and self.hist_win.winfo_exists():
            self.hist_win.destroy(); self.hist_win = None

    def _new_chat(self, e=None):
        for w in self.msgs.winfo_children(): w.destroy()
        self._add_msg("Started a new chat! How can I help?", "helios")
        if self.hist_win and self.hist_win.winfo_exists():
            self.hist_win.destroy(); self.hist_win = None

    def _clear_hist(self, e=None):
        if self.agent: self.agent.history.clear_all()
        if self.hist_win and self.hist_win.winfo_exists():
            self.hist_win.destroy(); self.hist_win = None

    def _switch_model(self, model: str):
        if not self.agent: return
        if model.startswith("gpt"):
            self.agent.llm.set_mode("online")
            self.agent.llm.set_cloud("gpt")
            self.agent.llm.openai_model = model
            lbl = f"☁ GPT · {model}"
        elif model.startswith("gemini"):
            self.agent.llm.set_mode("online")
            self.agent.llm.set_cloud("gemini")
            self.agent.llm.gemini_model = model
            lbl = f"✨ Gemini · {model}"
        else:
            self.agent.llm.set_model(model)
            self.agent.llm.set_mode("offline")
            lbl = f"🌿 LOCAL · {model}"
        self.status_lbl.configure(text=lbl)
        self._add_msg(f"✓ Switched to: {model}", "helios")
        if self.hist_win and self.hist_win.winfo_exists():
            self.hist_win.destroy(); self.hist_win = None

    def _switch_cloud(self, provider: str):
        if not self.agent: return
        self.agent.llm.set_cloud(provider)
        self._add_msg(f"☁ Cloud provider set to: {provider}", "helios")

    def _switch_mode(self, mode: str):
        if not self.agent: return
        self.agent.llm.set_mode(mode)
        self._add_msg(f"Mode set to: {mode}", "helios")

    # ── AGENT LOADER ──────────────────────────────────────────────────────
    def _load_agent(self):
        def _init():
            try:
                from agent import HELIOSAgent
                self.agent = HELIOSAgent()
                # Wire reminder notifications into the chat window
                self.agent.set_ui_notify(
                    lambda msg: self.root.after(0,
                        lambda m=msg: self._add_msg(m, 'helios')))
                s = self.agent.llm.status()
                cloud = ""
                if s.get("has_gemini_key"): cloud = " · Gemini ✓"
                elif s.get("has_openai_key"): cloud = " · GPT ✓"
                lbl = f"{'🌿 LOCAL' if s['ollama_alive'] else '⚠ Ollama offline'} · {s['local_model']}{cloud}"
                self.root.after(0, lambda: self.status_lbl.configure(text=lbl))
            except Exception as ex:
                msg = str(ex)
                def show(m=msg):
                    self.status_lbl.configure(text=f"⚠ Init failed")
                    self._add_msg(
                        f"Init failed: {m}\n\n"
                        f"Make sure Ollama is running:\n"
                        f"  ollama serve\n\n"
                        f"And psutil is installed:\n"
                        f"  pip install psutil", "helios")
                self.root.after(0, show)
        threading.Thread(target=_init, daemon=True).start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    HELIOSPopup().run()
