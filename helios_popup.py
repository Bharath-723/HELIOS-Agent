"""
HELIOS - Desktop Chat Popup
============================
Features
  🎤 Voice input  — click mic → speak → transcribed and sent automatically
  📎 File upload  — attach any doc / image / code file for HELIOS to analyse
  ⋮  Settings     — model, cloud, mode switcher + scrollable session history

Run
---
    python helios_popup.py

Voice dependencies (install once)
-----------------------------------
    pip install SpeechRecognition pyaudio
    # If pyaudio fails on Windows:
    pip install pipwin && pipwin install pyaudio
"""

import os
import queue
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

# ── Voice module (graceful fallback if not importable) ────────────────────────
try:
    from modules.voice_input import VoiceInput, VoiceResult
    _VOICE_AVAILABLE = True
except Exception:
    _VOICE_AVAILABLE = False
    VoiceInput  = None   # type: ignore
    VoiceResult = None   # type: ignore

# ── Colors ────────────────────────────────────────────────────────────────────
C = {
    "header":   "#4f46e5",
    "chat_bg":  "#f0f2f5",
    "user_bg":  "#4f46e5",
    "bot_bg":   "#ffffff",
    "input_bg": "#ffffff",
    "hist_bg":  "#1e1e2e",
    "hist_hdr": "#2a2a3e",
    "border":   "#e5e7eb",
    "send":     "#4f46e5",
    "fg_hdr":   "#ffffff",
    "fg_sub":   "#c7d2fe",
    "fg_user":  "#ffffff",
    "fg_bot":   "#111827",
    "fg_time":  "#9ca3af",
    "fg_dim":   "#888899",
    "fg_hist":  "#e0e0f0",
    "accent":   "#6366f1",
    "mic_idle": "#6366f1",
    "mic_live": "#ef4444",
    "file_bg":  "#f0f4ff",
    "file_bd":  "#6366f1",
}
F = lambda s, b="normal": ("Segoe UI", s, b)

# ── File-type sets ────────────────────────────────────────────────────────────
TEXT_EXTS = {
    ".txt", ".md", ".py", ".js", ".ts", ".html", ".css",
    ".json", ".csv", ".log", ".xml", ".yaml", ".yml",
    ".ini", ".cfg", ".bat", ".sh", ".java", ".c", ".cpp",
    ".h", ".cs", ".rb", ".go", ".rs", ".sql",
}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
DOC_EXTS   = {".pdf", ".docx", ".xlsx", ".xls", ".pptx"}
ALL_EXTS   = TEXT_EXTS | IMAGE_EXTS | DOC_EXTS

FILETYPES = [
    ("All supported",
     "*.txt *.md *.py *.js *.ts *.html *.css *.json *.csv *.log "
     "*.xml *.yaml *.yml *.pdf *.docx *.xlsx *.pptx "
     "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
    ("Text / Code",  "*.txt *.md *.py *.js *.csv *.json *.log *.html"),
    ("Documents",    "*.pdf *.docx *.xlsx *.pptx"),
    ("Images",       "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
    ("All files",    "*.*"),
]

# ─────────────────────────────────────────────────────────────────────────────
class HELIOSPopup:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HELIOS")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.97)
        self.root.configure(bg=C["chat_bg"])

        W, H = 370, 560
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{sw - W - 20}+{sh - H - 60}")
        self.root.resizable(False, False)

        # Core state
        self.agent        = None
        self.q:  queue.Queue = queue.Queue()

        # Drag state
        self._dx = self._dy = 0
        self._dragging   = False
        self._drag_sx = self._drag_sy = 0

        # Input state
        self._is_ph       = True
        self._anim_id     = None
        self.t_row        = None
        self.hist_win     = None

        # Voice state
        self._voice: VoiceInput | None = (
            VoiceInput(language="en-IN") if _VOICE_AVAILABLE else None
        )
        self._mic_active = False

        # File attachment state
        self._attached_file: str | None = None

        self._build()
        self._load_agent()
        self._poll()

    # ═════════════════════════════════════════════════════════════════════════
    # BUILD UI
    # ═════════════════════════════════════════════════════════════════════════
    def _build(self):
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        self._build_header()
        self._build_chat_area()
        self._build_divider()
        self._build_attach_bar()     # hidden by default (row 3)
        self._build_input_bar()      # row 4
        self._post_welcome()

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["header"], height=62)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)
        hdr.grid_propagate(False)

        # Avatar
        av = tk.Canvas(hdr, width=38, height=38, bg=C["header"],
                       highlightthickness=0)
        av.grid(row=0, column=0, padx=(10, 8), pady=12)
        av.create_oval(1, 1, 37, 37, fill=C["accent"], outline="#818cf8")
        av.create_text(19, 19, text="H", font=F(14, "bold"), fill="white")

        # Title / status
        tf = tk.Frame(hdr, bg=C["header"])
        tf.grid(row=0, column=1, sticky="w")
        tk.Label(tf, text="HELIOS", font=F(12, "bold"),
                 bg=C["header"], fg=C["fg_hdr"]).pack(anchor="w")
        self.status_lbl = tk.Label(tf, text="Initializing...",
                                    font=F(8), bg=C["header"], fg=C["fg_sub"])
        self.status_lbl.pack(anchor="w")

        # Window buttons  ⋮  ✕
        bf = tk.Frame(hdr, bg=C["header"])
        bf.grid(row=0, column=2, padx=8)

        self.dots_btn = tk.Label(bf, text="⋮", font=F(16), bg=C["header"],
                                  fg=C["fg_sub"], cursor="hand2")
        self.dots_btn.pack(side="left", padx=(0, 8))
        self.dots_btn.bind("<ButtonRelease-1>", self._on_dots_click)

        self.close_btn = tk.Label(bf, text="✕", font=F(13), bg=C["header"],
                                   fg=C["fg_sub"], cursor="hand2")
        self.close_btn.pack(side="left")
        self.close_btn.bind("<ButtonRelease-1>", self._on_close_click)

        # Drag bindings (only on non-interactive parts)
        for w in (hdr, av, tf):
            w.bind("<ButtonPress-1>",   self._drag_start)
            w.bind("<B1-Motion>",       self._drag_do)
            w.bind("<ButtonRelease-1>", self._drag_end)

    # ── Chat area ─────────────────────────────────────────────────────────────
    def _build_chat_area(self):
        cf = tk.Frame(self.root, bg=C["chat_bg"])
        cf.grid(row=1, column=0, sticky="nsew")
        cf.rowconfigure(0, weight=1)
        cf.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(cf, bg=C["chat_bg"], highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(cf, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self.msgs = tk.Frame(self.canvas, bg=C["chat_bg"])
        self._cw  = self.canvas.create_window((0, 0), window=self.msgs,
                                               anchor="nw")
        self.msgs.bind("<Configure>", lambda e:
            self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e:
            self.canvas.itemconfig(self._cw, width=e.width))
        self.canvas.bind_all("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def _build_divider(self):
        tk.Frame(self.root, bg=C["border"], height=1).grid(
            row=2, column=0, sticky="ew")

    # ── Attachment preview bar (row 3, hidden until file is picked) ───────────
    def _build_attach_bar(self):
        self.attach_bar = tk.Frame(self.root, bg=C["file_bg"],
                                    highlightthickness=1,
                                    highlightbackground=C["file_bd"])
        # Not gridded yet
        self.attach_lbl = tk.Label(self.attach_bar, text="",
                                    font=F(8), bg=C["file_bg"],
                                    fg=C["accent"], anchor="w")
        self.attach_lbl.pack(side="left", padx=(8, 4), pady=4)
        clr = tk.Label(self.attach_bar, text="✕", font=F(9),
                        bg=C["file_bg"], fg="#9ca3af", cursor="hand2")
        clr.pack(side="right", padx=6)
        clr.bind("<ButtonRelease-1>", lambda e: self._clear_attachment())

    # ── Input bar (row 4) ─────────────────────────────────────────────────────
    def _build_input_bar(self):
        inp = tk.Frame(self.root, bg=C["input_bg"])
        inp.grid(row=4, column=0, sticky="ew")
        inp.columnconfigure(1, weight=1)

        # Column 0 — 📎 attach button
        self.attach_btn = tk.Label(inp, text="📎", font=F(14),
                                    bg=C["input_bg"], fg="#9ca3af",
                                    cursor="hand2")
        self.attach_btn.grid(row=0, column=0, padx=(10, 4), pady=10)
        self.attach_btn.bind("<ButtonRelease-1>", lambda e: self._pick_file())

        # Column 1 — text entry
        self.entry = tk.Entry(inp, font=F(10), bg=C["input_bg"], fg="#9ca3af",
                               relief="flat", bd=0,
                               insertbackground=C["send"])
        self.entry.grid(row=0, column=1, sticky="ew", pady=12)
        self.entry.insert(0, "Write a message...")
        self.entry.bind("<FocusIn>",  self._ph_clear)
        self.entry.bind("<FocusOut>", self._ph_restore)
        self.entry.bind("<Return>",   self._send)

        # Column 2 — 🎤 mic button (canvas so we can redraw it)
        self.mic_c = tk.Canvas(inp, width=32, height=32, bg=C["input_bg"],
                                highlightthickness=0, cursor="hand2")
        self.mic_c.grid(row=0, column=2, padx=4, pady=10)
        self._draw_mic(idle=True)
        self.mic_c.bind("<ButtonRelease-1>", self._on_mic_click)

        # Column 3 — ➤ send button
        sc = tk.Canvas(inp, width=36, height=36, bg=C["input_bg"],
                        highlightthickness=0, cursor="hand2")
        sc.grid(row=0, column=3, padx=(2, 10), pady=8)
        sc.create_oval(2, 2, 34, 34, fill=C["send"], outline="")
        sc.create_text(18, 18, text="➤", font=F(11, "bold"), fill="white")
        sc.bind("<Button-1>", self._send)

    def _post_welcome(self):
        self._add_msg(
            "Hi! I'm HELIOS — your system control AI.\n\n"
            "  🎤 Click the mic and speak — I'll transcribe and act\n"
            "  📎 Click the clip to attach a file for analysis\n"
            "  ⌨  Or just type a command in plain English",
            "helios")

    # ═════════════════════════════════════════════════════════════════════════
    # DRAG
    # ═════════════════════════════════════════════════════════════════════════
    def _drag_start(self, e):
        self._dragging = False
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()
        self._drag_sx = e.x_root
        self._drag_sy = e.y_root

    def _drag_do(self, e):
        if abs(e.x_root - self._drag_sx) > 3 or abs(e.y_root - self._drag_sy) > 3:
            self._dragging = True
        if self._dragging:
            self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def _drag_end(self, e):
        self.root.after(50, lambda: setattr(self, "_dragging", False))

    def _on_dots_click(self, e):
        if not self._dragging:
            self._toggle_hist()

    def _on_close_click(self, e):
        if not self._dragging:
            if self.agent:
                try: self.agent.shutdown()
                except: pass
            self.root.destroy()

    # ═════════════════════════════════════════════════════════════════════════
    # PLACEHOLDER
    # ═════════════════════════════════════════════════════════════════════════
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

    # ═════════════════════════════════════════════════════════════════════════
    # MIC BUTTON
    # ═════════════════════════════════════════════════════════════════════════
    def _draw_mic(self, idle: bool = True):
        """Redraw the mic canvas icon. idle=True → indigo, False → red."""
        self.mic_c.delete("all")
        color = C["mic_idle"] if idle else C["mic_live"]
        # Background circle
        self.mic_c.create_oval(1, 1, 31, 31, fill=color, outline="")
        # Mic capsule body
        self.mic_c.create_rectangle(12, 6, 20, 19,
                                     fill="white", outline="white")
        # Mic arc (stand)
        self.mic_c.create_arc(8, 13, 24, 25,
                               start=0, extent=-180,
                               outline="white", width=2, style="arc")
        # Stem + base line
        self.mic_c.create_line(16, 25, 16, 28, fill="white", width=2)
        self.mic_c.create_line(12, 28, 20, 28, fill="white", width=2)

    def _on_mic_click(self, e):
        """Toggle voice recording on/off."""
        if not _VOICE_AVAILABLE or self._voice is None:
            self._set_status("⚠ Install: pip install SpeechRecognition pyaudio")
            return

        if self._mic_active:
            # Second click — stop early
            self._voice.stop()
            self._mic_active = False
            self._draw_mic(idle=True)
            self._set_status("Recording stopped.")
            return

        if not self.agent:
            self._set_status("⚠ Agent not ready yet.")
            return

        # Start recording
        self._mic_active = True
        self._draw_mic(idle=False)
        self._set_status("🎤 Listening… click again to stop")

        self._voice.start(callback=self._on_voice_result)

    def _on_voice_result(self, result: "VoiceResult"):
        """
        Called from the voice thread when recording + transcription finish.
        Must post to the main thread via queue — never touch Tkinter directly.
        """
        self._mic_active = False
        if result.success:
            self.q.put(("__voice__", result.text, result.engine))
        else:
            self.q.put(("__status__", f"⚠ {result.error}"))

    # ═════════════════════════════════════════════════════════════════════════
    # FILE ATTACHMENT
    # ═════════════════════════════════════════════════════════════════════════
    def _pick_file(self):
        path = filedialog.askopenfilename(
            title="Attach file for HELIOS to analyse",
            filetypes=FILETYPES,
        )
        if not path:
            return
        self._attached_file = path
        p   = Path(path)
        sz  = p.stat().st_size
        szs = f"{sz // 1024} KB" if sz >= 1024 else f"{sz} B"
        self.attach_lbl.configure(text=f"📄 {p.name}  [{szs}]")
        self.attach_bar.grid(row=3, column=0, sticky="ew")
        self.attach_btn.configure(fg=C["accent"])

    def _clear_attachment(self):
        self._attached_file = None
        self.attach_bar.grid_remove()
        self.attach_btn.configure(fg="#9ca3af")

    def _read_file_content(self, path: str) -> str:
        """
        Read file content into a string suitable for the LLM context.
        Handles: plain text, PDF, DOCX, XLSX, images.
        Max ~8 000 chars to stay within model context window.
        """
        p   = Path(path)
        ext = p.suffix.lower()

        # ── Plain text / code ────────────────────────────────────────────
        if ext in TEXT_EXTS:
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                if len(content) > 8000:
                    content = content[:8000] + f"\n\n...[truncated, {len(content)} chars total]"
                return f"[File: {p.name}]\n\n{content}"
            except Exception as exc:
                return f"[Could not read {p.name}: {exc}]"

        # ── PDF ──────────────────────────────────────────────────────────
        if ext == ".pdf":
            try:
                import PyPDF2
                with open(path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                pages = []
                for i, page in enumerate(reader.pages[:15]):
                    text = (page.extract_text() or "").strip()
                    if text:
                        pages.append(f"--- Page {i+1} ---\n{text}")
                content = "\n\n".join(pages)[:8000]
                return f"[PDF: {p.name}, {len(reader.pages)} pages]\n\n{content}"
            except ImportError:
                return f"[PDF: {p.name}]\nInstall PyPDF2: pip install PyPDF2"
            except Exception as exc:
                return f"[Could not read PDF {p.name}: {exc}]"

        # ── DOCX ─────────────────────────────────────────────────────────
        if ext == ".docx":
            try:
                import docx as docxlib
                doc  = docxlib.Document(path)
                text = "\n".join(para.text for para in doc.paragraphs
                                 if para.text.strip())[:8000]
                return f"[DOCX: {p.name}]\n\n{text}"
            except ImportError:
                return f"[DOCX: {p.name}]\nInstall python-docx: pip install python-docx"
            except Exception as exc:
                return f"[Could not read DOCX {p.name}: {exc}]"

        # ── XLSX / XLS ────────────────────────────────────────────────────
        if ext in (".xlsx", ".xls"):
            try:
                import openpyxl
                wb    = openpyxl.load_workbook(path, read_only=True, data_only=True)
                lines = []
                for sheet in wb.sheetnames[:3]:
                    ws = wb[sheet]
                    lines.append(f"=== Sheet: {sheet} ===")
                    for row in list(ws.iter_rows(values_only=True))[:50]:
                        row_str = " | ".join(
                            str(c) if c is not None else "" for c in row)
                        if row_str.strip(" |"):
                            lines.append(row_str)
                return f"[Excel: {p.name}]\n\n" + "\n".join(lines)[:8000]
            except ImportError:
                return f"[Excel: {p.name}]\nInstall openpyxl: pip install openpyxl"
            except Exception as exc:
                return f"[Could not read Excel {p.name}: {exc}]"

        # ── Images — Gemini Vision if available ───────────────────────────
        if ext in IMAGE_EXTS:
            try:
                sz  = p.stat().st_size
                szs = f"{sz // 1024} KB"
                try:
                    from PIL import Image as PILImage
                    img  = PILImage.open(path)
                    dims = f"{img.width}x{img.height}px, {img.mode}"
                except Exception:
                    dims = "dimensions unknown"

                if self.agent and self.agent.llm._has_gemini_key():
                    import base64
                    b64 = base64.b64encode(p.read_bytes()).decode()
                    return (f"[Image: {p.name}, {dims}, {szs}]\n"
                            f"__IMAGE_BASE64__:{ext.lstrip('.')}:{b64}")

                return (f"[Image: {p.name}, {dims}, {szs}]\n"
                        f"Describe the image or ask a question about it.\n"
                        f"(Add a Gemini API key for AI image analysis.)")
            except Exception as exc:
                return f"[Image: {p.name}] (error: {exc})"

        return (f"[File: {p.name}]\n"
                f"Unsupported type '{ext}'. Supported: text, PDF, DOCX, XLSX, images.")

    # ═════════════════════════════════════════════════════════════════════════
    # MESSAGES
    # ═════════════════════════════════════════════════════════════════════════
    def _add_msg(self, text: str, sender: str, tag: str = ""):
        ts      = datetime.now().strftime("%I:%M %p")
        is_user = sender == "user"

        row = tk.Frame(self.msgs, bg=C["chat_bg"])
        row.pack(fill="x", padx=10, pady=(6, 0))

        lines = sum(max(1, -(-len(p) // 34)) for p in text.split("\n"))
        lines = max(1, min(lines, 30))

        txt = tk.Text(row, font=F(10),
                      bg=C["user_bg"] if is_user else C["bot_bg"],
                      fg=C["fg_user"] if is_user else C["fg_bot"],
                      relief="flat", bd=0, padx=12, pady=8,
                      wrap="word", width=34, height=lines,
                      cursor="xterm", exportselection=True)
        txt.insert("1.0", text)
        txt.configure(state="disabled")

        # Right-click copy menu
        menu = tk.Menu(txt, tearoff=0)
        menu.add_command(label="Copy selected",
                         command=lambda t=txt: self._copy_sel(t))
        menu.add_command(label="Copy all",
                         command=lambda t=txt: self._copy_all(t))
        txt.bind("<Button-3>", lambda e, m=menu: m.post(e.x_root, e.y_root))

        def enable_sel(e, t=txt):
            t.configure(state="normal")
            t.after(1, lambda: t.configure(state="disabled"))
        txt.bind("<Button-1>", enable_sel)

        if is_user:
            txt.pack(anchor="e")
        else:
            txt.configure(highlightthickness=1,
                          highlightbackground=C["border"],
                          highlightcolor=C["border"])
            txt.pack(anchor="w")

        # Timestamp + optional tag row
        rb = tk.Frame(row, bg=C["chat_bg"])
        rb.pack(fill="x")
        if tag:
            tk.Label(rb, text=tag, font=F(7), bg=C["chat_bg"],
                     fg=C["accent"]).pack(
                side="right" if is_user else "left")
        tk.Label(rb, text=ts, font=F(7), bg=C["chat_bg"],
                 fg=C["fg_time"]).pack(
            side="right" if is_user else "left", padx=4)

        self.root.after(150, lambda: self.canvas.yview_moveto(1.0))

    def _copy_sel(self, t):
        try:
            s = t.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(s)
        except tk.TclError:
            pass

    def _copy_all(self, t):
        self.root.clipboard_clear()
        self.root.clipboard_append(t.get("1.0", tk.END).strip())

    # ═════════════════════════════════════════════════════════════════════════
    # TYPING INDICATOR
    # ═════════════════════════════════════════════════════════════════════════
    def _show_typing(self):
        self.t_row = tk.Frame(self.msgs, bg=C["chat_bg"])
        self.t_row.pack(fill="x", padx=10, pady=(6, 0))
        self._tlbl = tk.Label(self.t_row, text="●  ○  ○  thinking",
                               font=("Segoe UI", 9, "italic"),
                               bg=C["bot_bg"], fg="#6b7280",
                               padx=10, pady=6)
        self._tlbl.pack(anchor="w")
        self._anim(0)
        self.root.after(150, lambda: self.canvas.yview_moveto(1.0))

    def _anim(self, n):
        frames = ["●  ○  ○", "●  ●  ○", "●  ●  ●", "○  ●  ●", "○  ○  ●"]
        if self.t_row and self.t_row.winfo_exists():
            self._tlbl.configure(text=f"{frames[n % 5]}  thinking")
            self._anim_id = self.root.after(350, self._anim, n + 1)

    def _hide_typing(self):
        if self._anim_id:
            self.root.after_cancel(self._anim_id)
            self._anim_id = None
        if self.t_row and self.t_row.winfo_exists():
            self.t_row.destroy()
            self.t_row = None

    # ═════════════════════════════════════════════════════════════════════════
    # SEND / RECEIVE
    # ═════════════════════════════════════════════════════════════════════════
    def _send(self, e=None):
        """Read entry + optional file attachment, dispatch to agent."""
        raw_text  = self.entry.get().strip()
        text      = "" if self._is_ph else raw_text
        file_path = self._attached_file

        if not text and not file_path:
            return
        if not self.agent:
            return

        # Build display string and metadata tag
        file_name = Path(file_path).name if file_path else ""
        if file_path and text:
            display = f"[{file_name}]\n{text}"
            tag     = f"📎 {file_name}"
        elif file_path:
            display = f"[{file_name}]"
            tag     = f"📎 {file_name}"
        else:
            display = text
            tag     = ""

        # Reset UI
        self.entry.delete(0, tk.END)
        self._is_ph = False
        self._clear_attachment()

        self._add_msg(display, "user", tag=tag)
        self._show_typing()

        threading.Thread(
            target=self._bg_process,
            args=(text, file_path),
            daemon=True,
        ).start()

    def _bg_process(self, text: str, file_path: str | None):
        """Run agent.process() in background, post result to queue."""
        try:
            if file_path:
                content = self._read_file_content(file_path)
                if "__IMAGE_BASE64__" in content:
                    resp = self._call_gemini_vision(file_path, content, text)
                else:
                    combined = (
                        f"{content}\n\n"
                        + (f"User question: {text}" if text else
                           "Please analyse this file and summarise the key content.")
                    )
                    resp = self.agent.process(combined)
            else:
                resp = self.agent.process(text)
        except Exception as exc:
            resp = f"Error: {exc}"
        self.q.put(("__msg__", resp))

    def _call_gemini_vision(self, path: str,
                             content: str, question: str) -> str:
        """Send image to Gemini Vision via REST and return description."""
        try:
            import requests
            marker = "__IMAGE_BASE64__:"
            after  = content[content.index(marker) + len(marker):]
            ext_part, b64 = after.split(":", 1)
            prompt = question or "Describe this image in detail."
            url    = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-2.0-flash:generateContent"
                f"?key={self.agent.llm.gemini_key}"
            )
            payload = {"contents": [{"parts": [
                {"text": prompt},
                {"inline_data": {
                    "mime_type": f"image/{ext_part}",
                    "data": b64,
                }},
            ]}]}
            r = requests.post(url, json=payload, timeout=30)
            if r.status_code == 200:
                return (r.json()
                        .get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "No description returned."))
            err = r.json().get("error", {}).get("message", r.text)
            return f"Image analysis failed: {err}"
        except Exception as exc:
            return (f"Image uploaded: {Path(path).name}\n"
                    f"Vision analysis unavailable: {exc}")

    # ═════════════════════════════════════════════════════════════════════════
    # POLL QUEUE  (all cross-thread UI updates come through here)
    # ═════════════════════════════════════════════════════════════════════════
    def _poll(self):
        try:
            while True:
                item = self.q.get_nowait()
                kind = item[0] if isinstance(item, tuple) else "__msg__"
                data = item[1] if isinstance(item, tuple) else item

                if kind == "__msg__":
                    # Agent response — show in chat
                    self._hide_typing()
                    self._add_msg(data, "helios")

                elif kind == "__voice__":
                    # Transcribed text — fill entry and auto-send
                    engine = item[2] if len(item) > 2 else ""
                    self._draw_mic(idle=True)
                    self._set_status(f"🎤 Heard: \"{data}\"")
                    self.entry.delete(0, tk.END)
                    self.entry.insert(0, data)
                    self.entry.configure(fg="#374151")
                    self._is_ph = False
                    # Brief delay so user sees the transcription, then send
                    tag = f"🎤 {engine}" if engine else "🎤 Voice"
                    self.root.after(500, lambda t=tag: self._send_voice(tag=t))

                elif kind == "__status__":
                    # Status bar update (mic errors, etc.)
                    self._draw_mic(idle=True)
                    self._set_status(data)

        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _send_voice(self, tag: str = "🎤 Voice"):
        """Same as _send() but forces a tag label on the bubble."""
        raw_text = self.entry.get().strip()
        text     = "" if self._is_ph else raw_text
        if not text or not self.agent:
            return
        self.entry.delete(0, tk.END)
        self._is_ph = False
        self._add_msg(text, "user", tag=tag)
        self._show_typing()
        threading.Thread(
            target=self._bg_process,
            args=(text, None),
            daemon=True,
        ).start()

    # ═════════════════════════════════════════════════════════════════════════
    # HISTORY / SETTINGS PANEL
    # ═════════════════════════════════════════════════════════════════════════
    def _toggle_hist(self):
        if self.hist_win and self.hist_win.winfo_exists():
            self.hist_win.destroy()
            self.hist_win = None
            return
        if not self.agent:
            return
        self._open_hist()

    def _open_hist(self):
        px, py = self.root.winfo_x(), self.root.winfo_y()
        self.hist_win = tk.Toplevel(self.root)
        self.hist_win.title("Settings")
        self.hist_win.overrideredirect(True)
        self.hist_win.attributes("-topmost", True)
        self.hist_win.geometry(f"275x540+{px - 280}+{py}")
        self.hist_win.configure(bg=C["hist_bg"])

        # Header
        hdr = tk.Frame(self.hist_win, bg=C["hist_hdr"], height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  Settings & History", font=F(11, "bold"),
                 bg=C["hist_hdr"], fg=C["fg_hist"]).pack(side="left", pady=14)
        cl = tk.Label(hdr, text="✕", font=F(12), bg=C["hist_hdr"],
                      fg=C["fg_dim"], cursor="hand2")
        cl.pack(side="right", padx=10)
        cl.bind("<ButtonRelease-1>", lambda e: self.hist_win.destroy())

        # Model switcher
        self._hist_section(self.hist_win)

        # Sessions list (scrollable)
        tk.Label(self.hist_win, text="  Recent sessions",
                 font=F(8), bg=C["hist_hdr"], fg=C["fg_dim"]).pack(
            fill="x", padx=8, pady=(4, 0))

        lf = tk.Frame(self.hist_win, bg=C["hist_bg"])
        lf.pack(fill="both", expand=True, padx=4)
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

        cv  = tk.Canvas(lf, bg=C["hist_bg"], highlightthickness=0)
        vsb = tk.Scrollbar(lf, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=vsb.set)
        cv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        inner  = tk.Frame(cv, bg=C["hist_bg"])
        win_id = cv.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",
                lambda e: cv.itemconfig(win_id, width=e.width))
        cv.bind("<MouseWheel>",
                lambda e: cv.yview_scroll(int(-1*(e.delta/120)), "units"))

        sessions = self.agent.history.get_all()
        if not sessions:
            tk.Label(inner, text="No history yet.", font=F(9),
                     bg=C["hist_bg"], fg="#555577", pady=20).pack()
        else:
            for s in sessions:
                self._hist_item(inner, s)

        # Footer
        tk.Frame(self.hist_win, bg="#333344", height=1).pack(fill="x")
        clr = tk.Label(self.hist_win, text="Clear All History",
                       font=F(9), bg=C["hist_bg"], fg="#ff6b6b",
                       cursor="hand2", pady=6)
        clr.pack()
        clr.bind("<ButtonRelease-1>", self._clear_hist)

    def _hist_section(self, parent):
        """Model / cloud / mode selectors + New Chat button."""
        # Model
        tk.Frame(parent, bg="#333344", height=1).pack(fill="x")
        msf = tk.Frame(parent, bg=C["hist_hdr"], pady=5)
        msf.pack(fill="x")
        tk.Label(msf, text="  Model:", font=F(9),
                 bg=C["hist_hdr"], fg=C["fg_dim"]).pack(side="left")
        self.model_var = tk.StringVar(value=self.agent.llm.ollama_model)
        available = self.agent.llm.get_available_models() or [self.agent.llm.ollama_model]
        om = tk.OptionMenu(msf, self.model_var, *available,
                           command=self._switch_model)
        om.configure(font=F(8), bg="#333355", fg="#c0c0e0",
                     activebackground="#4444aa", relief="flat",
                     highlightthickness=0, width=16)
        om["menu"].configure(bg="#333355", fg="#c0c0e0", font=F(9))
        om.pack(side="left", padx=6)

        # Cloud
        tk.Frame(parent, bg="#333344", height=1).pack(fill="x")
        cpf = tk.Frame(parent, bg=C["hist_hdr"], pady=4)
        cpf.pack(fill="x")
        tk.Label(cpf, text="  Cloud:", font=F(9),
                 bg=C["hist_hdr"], fg=C["fg_dim"]).pack(side="left")
        self.cloud_var = tk.StringVar(value=self.agent.llm.cloud_provider)
        for cp in ("gemini", "gpt"):
            has = (self.agent.llm._has_gemini_key() if cp == "gemini"
                   else self.agent.llm._has_openai_key())
            tk.Radiobutton(
                cpf, text=f"{'✓' if has else '✗'} {cp}",
                variable=self.cloud_var, value=cp,
                command=lambda c=cp: self._switch_cloud(c),
                font=F(8), bg=C["hist_hdr"],
                fg="#22c55e" if has else "#ef4444",
                selectcolor=C["hist_hdr"],
                activebackground=C["hist_hdr"],
            ).pack(side="left", padx=6)

        # Mode
        tk.Frame(parent, bg="#333344", height=1).pack(fill="x")
        mdf = tk.Frame(parent, bg=C["hist_hdr"], pady=4)
        mdf.pack(fill="x")
        tk.Label(mdf, text="  Mode:", font=F(9),
                 bg=C["hist_hdr"], fg=C["fg_dim"]).pack(side="left")
        self.mode_var = tk.StringVar(value=self.agent.llm.mode)
        for m in ("offline", "auto", "online"):
            tk.Radiobutton(
                mdf, text=m, variable=self.mode_var, value=m,
                command=lambda mv=m: self._switch_mode(mv),
                font=F(8), bg=C["hist_hdr"], fg=C["fg_hist"],
                selectcolor=C["hist_hdr"], activebackground=C["hist_hdr"],
            ).pack(side="left", padx=4)

        # New chat
        tk.Frame(parent, bg="#333344", height=1).pack(fill="x")
        nc = tk.Label(parent, text="  + New Chat", font=F(10),
                      bg=C["accent"], fg="white", cursor="hand2", pady=6)
        nc.pack(fill="x", padx=8, pady=5)
        nc.bind("<ButtonRelease-1>", self._new_chat)

    def _hist_item(self, parent, session: dict):
        sid   = session.get("id", "")
        title = session.get("title", sid)
        ts    = session.get("started", "")[:16].replace("T", " ")
        count = session.get("message_count", 0)

        item = tk.Frame(parent, bg=C["hist_hdr"], cursor="hand2")
        item.pack(fill="x", padx=4, pady=2)
        tk.Label(item, text=title, font=F(9, "bold"), bg=C["hist_hdr"],
                 fg=C["fg_hist"], wraplength=220, justify="left").pack(
            anchor="w", padx=8, pady=(5, 1))
        tk.Label(item, text=f"{ts}  ·  {count} msgs", font=F(7),
                 bg=C["hist_hdr"], fg="#555577").pack(
            anchor="w", padx=8, pady=(0, 5))

        def enter(e):  item.configure(bg="#333366")
        def leave(e):  item.configure(bg=C["hist_hdr"])
        def click(e):  self._load_sess(sid)

        for w in (item, *item.winfo_children()):
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<ButtonRelease-1>", click)

    def _load_sess(self, sid: str):
        if not self.agent: return
        msgs = self.agent.history.load(sid)
        for w in self.msgs.winfo_children():
            w.destroy()
        for m in msgs:
            self._add_msg(m["content"], m["role"])
        if self.hist_win and self.hist_win.winfo_exists():
            self.hist_win.destroy()
            self.hist_win = None

    def _new_chat(self, e=None):
        for w in self.msgs.winfo_children():
            w.destroy()
        self._add_msg("New session! How can I help?", "helios")
        if self.hist_win and self.hist_win.winfo_exists():
            self.hist_win.destroy()
            self.hist_win = None

    def _clear_hist(self, e=None):
        if self.agent:
            self.agent.history.clear_all()
        if self.hist_win and self.hist_win.winfo_exists():
            self.hist_win.destroy()
            self.hist_win = None

    # ── Model / mode switchers ────────────────────────────────────────────────
    def _switch_model(self, model: str):
        if not self.agent: return
        if model.startswith("gpt"):
            self.agent.llm.set_mode("online")
            self.agent.llm.set_cloud("gpt")
            self.agent.llm.openai_model = model
            lbl = f"GPT · {model}"
        elif model.startswith("gemini"):
            self.agent.llm.set_mode("online")
            self.agent.llm.set_cloud("gemini")
            self.agent.llm.gemini_model = model
            lbl = f"Gemini · {model}"
        else:
            self.agent.llm.set_model(model)
            self.agent.llm.set_mode("offline")
            lbl = f"Local · {model}"
        self.status_lbl.configure(text=lbl)
        self._add_msg(f"Switched to: {model}", "helios")
        if self.hist_win and self.hist_win.winfo_exists():
            self.hist_win.destroy()
            self.hist_win = None

    def _switch_cloud(self, provider: str):
        if not self.agent: return
        self.agent.llm.set_cloud(provider)
        self._add_msg(f"Cloud: {provider}", "helios")

    def _switch_mode(self, mode: str):
        if not self.agent: return
        self.agent.llm.set_mode(mode)
        self._add_msg(f"Mode: {mode}", "helios")

    # ── Status bar helper ─────────────────────────────────────────────────────
    def _set_status(self, text: str):
        self.status_lbl.configure(text=text)

    def _restore_status(self):
        if not self.agent: return
        s     = self.agent.llm.status()
        cloud = (" · Gemini ✓" if s.get("has_gemini_key") else
                 " · GPT ✓"   if s.get("has_openai_key")  else "")
        self._set_status(
            f"{'LOCAL' if s['ollama_alive'] else 'Ollama offline'}"
            f" · {s['local_model']}{cloud}"
        )

    # ═════════════════════════════════════════════════════════════════════════
    # AGENT LOADER
    # ═════════════════════════════════════════════════════════════════════════
    def _load_agent(self):
        def _init():
            try:
                from agent import HELIOSAgent
                self.agent = HELIOSAgent()
                # Wire reminder notifications into the chat window
                self.agent.set_ui_notify(
                    lambda msg: self.root.after(
                        0, lambda m=msg: self._add_msg(m, "helios")))
                self.root.after(0, self._restore_status)
            except Exception as exc:
                msg = str(exc)
                def show(m=msg):
                    self._set_status("Init failed")
                    self._add_msg(
                        f"Init failed: {m}\n\nMake sure Ollama is running:\n  ollama serve",
                        "helios")
                self.root.after(0, show)

        threading.Thread(target=_init, daemon=True).start()

    # ═════════════════════════════════════════════════════════════════════════
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    HELIOSPopup().run()