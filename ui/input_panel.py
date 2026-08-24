"""
ui/input_panel.py — HELIOS Floating Glass Command Dock
======================================================
Elevated command input dock with:
  - Overlay read-only placeholder (never literal text inside Entry)
  - Real Voice Input Recording via PyAudio + SpeechRecognition / Whisper
  - Dynamic Model Selector pill ([ MODEL: AUTO ▼ ])
  - Discovers Ollama local models AND configured Cloud models (Gemini / OpenAI)
"""

from __future__ import annotations
import threading
import tkinter as tk
from .theme import C, F, ThemeManager


class InputPanel:
    """Floating capsule command dock with overlay placeholder, real STT voice recording, and model selector."""

    def __init__(self, parent: tk.Widget,
                 on_send: callable,
                 on_voice_result: callable,
                 on_status: callable,
                 on_model_change: callable = None,
                 on_auto_toggle: callable = None) -> None:

        self._parent          = parent
        self._on_send         = on_send
        self._on_voice_result = on_voice_result
        self._on_status       = on_status
        self._on_model_change = on_model_change
        self._on_auto_toggle  = on_auto_toggle

        self._active_model  = "gemma3"
        self._is_auto       = True
        self._dropdown_win: tk.Frame | None = None
        self._attached_files: list[str] = []

        # Voice recording state
        self._is_listening  = False
        self._voice_instance = None
        self._mic_canvas: tk.Canvas | None = None

        self.frame = tk.Frame(parent, bg=C.BG)
        self._build()
        ThemeManager.add_listener(self._on_theme_changed)

    def _build(self) -> None:
        dock_outer = tk.Frame(self.frame, bg=C.BG)
        dock_outer.pack(fill="x", side="top", padx=14, pady=(4, 6))

        # Floating glass container
        self.dock = tk.Frame(dock_outer, bg=C.GLASS_3, highlightthickness=1, highlightbackground=C.GLASS_BD_3)
        self.dock.pack(fill="x")

        # Attachment Chip Preview Container
        self._attach_frame = tk.Frame(self.dock, bg=C.GLASS_3, padx=8, pady=2)
        # Note: packed dynamically when attachments exist

        self.row = tk.Frame(self.dock, bg=C.GLASS_3, padx=8, pady=6)
        self.row.pack(fill="x")

        # Left tools: Attach (+), Camera (📷)
        self._make_tool_btn(self.row, "+", self._pick_files, C.CYAN)
        self._make_tool_btn(self.row, "📷", self._trigger_camera, C.VIOLET)

        # Right tools (packed right-to-left): Send (➤), Mic (🎤), Model Selector Pill
        send_btn = self._make_send_button(self.row, cmd=self._submit)
        send_btn.pack(side="right", padx=(4, 0))

        self._mic_canvas = self._make_tool_btn(self.row, "🎤", self._trigger_voice, C.WARN, side="right")

        self.model_pill = tk.Frame(self.row, bg=C.GLASS_4, cursor="hand2", padx=2, pady=2,
                                   highlightthickness=1, highlightbackground=C.GLASS_BD_4)
        self.model_pill.pack(side="right", padx=4)

        self.model_lbl = tk.Label(self.model_pill, text="MODEL: AUTO ▼",
                                  font=(F._PRIMARY, F.XS, "bold"),
                                  bg=C.GLASS_4, fg=C.BLUE_L, padx=6, pady=4)
        self.model_lbl.pack()

        for w in (self.model_pill, self.model_lbl):
            w.bind("<ButtonRelease-1>", lambda e: self._toggle_model_dropdown())

        # Center Command Entry container (expands to fill remaining space)
        self.entry_container = tk.Frame(self.row, bg=C.GLASS_1, highlightthickness=1, highlightbackground=C.BORDER)
        self.entry_container.pack(side="left", fill="x", expand=True, padx=6)

        # Command Entry (strictly EMPTY — no placeholder string inserted)
        self.entry = tk.Entry(self.entry_container, font=(F._FALLBACK, F.MD),
                               bg=C.GLASS_1, fg=C.FG_1,
                               insertbackground=C.BLUE, relief="flat", bd=0)
        self.entry.pack(fill="x", expand=True, padx=8, pady=6)

        # Overlay placeholder label
        self.ph_label = tk.Label(self.entry_container,
                                 text="Write a command or ask HELIOS...",
                                 font=(F._FALLBACK, F.MD),
                                 bg=C.GLASS_1, fg=C.FG_3, anchor="w", cursor="xterm")
        self.ph_label.place(x=8, y=6, relwidth=0.9, relheight=0.75)

        # Bind placeholder events
        self.ph_label.bind("<Button-1>", lambda e: self.entry.focus_set())
        self.entry.bind("<FocusIn>", self._on_entry_focus)
        self.entry.bind("<FocusOut>", self._on_entry_blur)
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<Return>", lambda e: self._submit())

    def _make_tool_btn(self, parent: tk.Widget, char: str, cmd: callable, fg_color: str, side: str = "left") -> tk.Canvas:
        cv = tk.Canvas(parent, width=32, height=32, bg=C.GLASS_3, highlightthickness=0, cursor="hand2")
        cv.pack(side=side, padx=2)

        def _draw(bg_col, bd_col):
            cv.delete("all")
            cv.create_oval(2, 2, 30, 30, fill=bg_col, outline=bd_col)
            cv.create_text(16, 16, text=char, font=(F._PRIMARY, F.SM, "bold"), fill=fg_color)

        _draw(C.GLASS_2, C.GLASS_BD_2)

        def _enter(e):
            if not (char == "🎤" and self._is_listening):
                _draw(C.BG_HOVER, C.BLUE)
        def _leave(e):
            if char == "🎤" and self._is_listening:
                _draw(C.WARN, C.WARN)
            else:
                _draw(C.GLASS_2, C.GLASS_BD_2)
        def _click(e):
            if cmd: cmd()

        cv.bind("<Enter>", _enter)
        cv.bind("<Leave>", _leave)
        cv.bind("<ButtonRelease-1>", _click)
        cv._redraw = _draw
        return cv

    def _make_send_button(self, parent: tk.Widget, cmd: callable) -> tk.Widget:
        btn_frame = tk.Frame(parent, bg=C.BLUE_D, bd=0, cursor="hand2")

        inner = tk.Frame(btn_frame, bg=C.BLUE, highlightthickness=1, highlightbackground=C.BLUE_L)
        inner.pack(fill="both", expand=True, padx=(0, 1), pady=(0, 1.5))

        lbl = tk.Label(inner, text="➤", font=(F._PRIMARY, F.SM, "bold"), bg=C.BLUE, fg="#FFFFFF", padx=12, pady=5)
        lbl.pack()

        def _press(e):
            inner.pack_configure(padx=(1, 0), pady=(1.5, 0))

        def _release(e):
            inner.pack_configure(padx=(0, 1), pady=(0, 1.5))
            if cmd: cmd()

        for w in (btn_frame, inner, lbl):
            w.bind("<Button-1>", _press)
            w.bind("<ButtonRelease-1>", _release)

        return btn_frame

    # ── Placeholder logic ──────────────────────────────────────────────────────
    def _on_entry_focus(self, e) -> None:
        self.ph_label.place_forget()

    def _on_entry_blur(self, e) -> None:
        if not self.entry.get().strip():
            self.ph_label.place(x=8, y=6, relwidth=0.9, relheight=0.75)

    def _on_key_release(self, e) -> None:
        if self.entry.get():
            self.ph_label.place_forget()
        else:
            self.ph_label.place(x=8, y=6, relwidth=0.9, relheight=0.75)

    # ── Model Dropdown Drawer ─────────────────────────────────────────────────
    def _toggle_model_dropdown(self) -> None:
        if self._dropdown_win:
            self._close_model_dropdown()
            return

        # Place dropdown frame right above input dock
        self._dropdown_win = tk.Frame(self._parent, bg=C.GLASS_4,
                                      highlightthickness=1, highlightbackground=C.BLUE,
                                      padx=8, pady=8)
        
        # Header
        hdr = tk.Frame(self._dropdown_win, bg=C.GLASS_4)
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text="MODEL SELECTION", font=(F._PRIMARY, F.XS, "bold"), bg=C.GLASS_4, fg=C.FG_1).pack(side="left")

        # Auto Option
        auto_btn = tk.Label(self._dropdown_win,
                            text="●  AUTO  (CAHRA Smart Routing)",
                            font=(F._PRIMARY, F.SM, "bold" if self._is_auto else "normal"),
                            bg=C.BG_ACTIVE if self._is_auto else C.GLASS_4,
                            fg=C.BLUE_L if self._is_auto else C.FG_2,
                            anchor="w", cursor="hand2", padx=8, pady=5)
        auto_btn.pack(fill="x", pady=2)
        auto_btn.bind("<ButtonRelease-1>", lambda e: self._select_model("AUTO", True))

        tk.Frame(self._dropdown_win, bg=C.BORDER, height=1).pack(fill="x", pady=4)

        # Local Models Section
        tk.Label(self._dropdown_win, text="LOCAL MODELS (Ollama)", font=(F._FALLBACK, F.XS, "bold"), bg=C.GLASS_4, fg=C.FG_3, anchor="w").pack(fill="x")
        
        self.local_container = tk.Frame(self._dropdown_win, bg=C.GLASS_4)
        self.local_container.pack(fill="x", pady=2)

        tk.Frame(self._dropdown_win, bg=C.BORDER, height=1).pack(fill="x", pady=4)
        tk.Label(self._dropdown_win, text="CLOUD MODELS", font=(F._FALLBACK, F.XS, "bold"), bg=C.GLASS_4, fg=C.FG_3, anchor="w").pack(fill="x")
        
        self.cloud_container = tk.Frame(self._dropdown_win, bg=C.GLASS_4)
        self.cloud_container.pack(fill="x", pady=2)

        # Fetch models async
        threading.Thread(target=self._fetch_models, daemon=True).start()

        # Position dropdown right above input dock
        rx = self.frame.winfo_rootx() - self._parent.winfo_rootx() + 300
        ry = self.frame.winfo_rooty() - self._parent.winfo_rooty() - 250
        self._dropdown_win.place(x=max(10, rx), y=max(10, ry), width=250)
        self._dropdown_win.lift()

    def _fetch_models(self) -> None:
        local_models = ["gemma3"]
        cloud_models = []
        try:
            from core.llm_engine import HybridLLM
            llm = HybridLLM()
            st = llm.status()
            avail = st.get("available_models", [])
            local_models = [m for m in avail if not (m.startswith("gemini") or m.startswith("gpt"))]
            if not local_models:
                local_models = ["gemma3"]
            cloud_models = [m for m in avail if (m.startswith("gemini") or m.startswith("gpt"))]
        except Exception:
            pass

        def _update_ui():
            if not self._dropdown_win:
                return
            # Update Local container
            for w in self.local_container.winfo_children():
                w.destroy()
            for m in local_models:
                is_sel = (m.lower() == self._active_model.lower()) and not self._is_auto
                btn = tk.Label(self.local_container,
                               text=f"●  {m.capitalize()}  · Local",
                               font=(F._PRIMARY, F.SM, "bold" if is_sel else "normal"),
                               bg=C.BG_ACTIVE if is_sel else C.GLASS_4,
                               fg=C.OK if is_sel else C.FG_2,
                               anchor="w", cursor="hand2", padx=8, pady=4)
                btn.pack(fill="x", pady=1)
                btn.bind("<ButtonRelease-1>", lambda e, mid=m: self._select_model(mid, False))

            # Update Cloud container
            for w in self.cloud_container.winfo_children():
                w.destroy()
            if cloud_models:
                for cm in cloud_models:
                    is_sel = (cm.lower() == self._active_model.lower()) and not self._is_auto
                    btn = tk.Label(self.cloud_container,
                                   text=f"●  {cm}  · Cloud",
                                   font=(F._PRIMARY, F.SM, "bold" if is_sel else "normal"),
                                   bg=C.BG_ACTIVE if is_sel else C.GLASS_4,
                                   fg=C.BLUE_L if is_sel else C.FG_2,
                                   anchor="w", cursor="hand2", padx=8, pady=4)
                    btn.pack(fill="x", pady=1)
                    btn.bind("<ButtonRelease-1>", lambda e, mid=cm: self._select_model(mid, False))
            else:
                tk.Label(self.cloud_container, text="No cloud provider is currently configured",
                         font=(F._FALLBACK, F.XS), bg=C.GLASS_4, fg=C.FG_3, anchor="w", padx=8, pady=4).pack(fill="x")

        self.frame.after(0, _update_ui)

    def _close_model_dropdown(self) -> None:
        if self._dropdown_win:
            try:
                self._dropdown_win.destroy()
            except Exception:
                pass
            self._dropdown_win = None

    def _select_model(self, model_id: str, is_auto: bool) -> None:
        self._close_model_dropdown()
        self._is_auto = is_auto
        if not is_auto:
            self._active_model = model_id

        lbl_text = "MODEL: AUTO ▼" if is_auto else f"MODEL: {model_id.upper()} ▼"
        self.model_lbl.configure(text=lbl_text, fg=C.BLUE_L if is_auto else C.OK)

        if is_auto and self._on_auto_toggle:
            self._on_auto_toggle()
        elif not is_auto and self._on_model_change:
            self._on_model_change(model_id)

    # ── Voice Recording STT Pipeline ─────────────────────────────────────────
    def _trigger_voice(self) -> None:
        """One-click non-blocking microphone audio capture & transcription."""
        if self._is_listening:
            # Stop early
            if self._voice_instance:
                self._voice_instance.stop()
            self._is_listening = False
            if self._mic_canvas and hasattr(self._mic_canvas, "_redraw"):
                self._mic_canvas._redraw(C.GLASS_2, C.GLASS_BD_2)
            if self._on_status:
                self._on_status("Voice recording stopped.")
            return

        try:
            from modules.voice_input import VoiceInput
            if not VoiceInput.is_available():
                ready_err = VoiceInput().ready_error()
                if self._on_status:
                    self._on_status(f"⚠ Voice unavailable: {ready_err.splitlines()[0]}")
                return

            self._is_listening = True
            if self._mic_canvas and hasattr(self._mic_canvas, "_redraw"):
                self._mic_canvas._redraw(C.WARN, C.WARN)
            if self._on_status:
                self._on_status("🎙 LISTENING... Speak now into microphone")

            self._voice_instance = VoiceInput(language="en-IN", timeout=6, phrase_limit=12)
            self._voice_instance.start(callback=self._on_voice_complete_bg)
        except Exception as exc:
            self._is_listening = False
            if self._mic_canvas and hasattr(self._mic_canvas, "_redraw"):
                self._mic_canvas._redraw(C.GLASS_2, C.GLASS_BD_2)
            if self._on_status:
                self._on_status(f"⚠ Mic error: {exc}")

    def _on_voice_complete_bg(self, result) -> None:
        """Daemon thread callback -> schedules UI update on Tkinter main thread."""
        self.frame.after(0, lambda: self._handle_voice_result(result))

    def _handle_voice_result(self, result) -> None:
        self._is_listening = False
        if self._mic_canvas and hasattr(self._mic_canvas, "_redraw"):
            self._mic_canvas._redraw(C.GLASS_2, C.GLASS_BD_2)

        if result.success and result.text:
            text = result.text.strip()
            self.set_text(text)
            if self._on_status:
                self._on_status(f"🎙 Heard: \"{text}\" ({result.engine})")
            
            # Pass transcript to handler or submit to HELIOS pipeline
            if self._on_voice_result:
                self._on_voice_result(text)
            self._submit()
        else:
            err = result.error.splitlines()[0] if result.error else "No speech detected"
            if self._on_status:
                self._on_status(f"⚠ Voice: {err}")

    # ── Actions ───────────────────────────────────────────────────────────────
    def attach_file(self, file_path: str) -> None:
        """Attach file/photo and display interactive preview chip."""
        if file_path and file_path not in self._attached_files:
            self._attached_files.append(file_path)
            self._render_attachment_chips()
            if self._on_status:
                self._on_status(f"📷 Attached: {Path(file_path).name}")
            self.entry.focus_set()

    def remove_attachment(self, file_path: str) -> None:
        if file_path in self._attached_files:
            self._attached_files.remove(file_path)
            self._render_attachment_chips()

    def _render_attachment_chips(self) -> None:
        for w in self._attach_frame.winfo_children():
            w.destroy()

        if not self._attached_files:
            self._attach_frame.pack_forget()
            return

        self._attach_frame.pack(fill="x", side="top", before=self.row)

        for path_str in self._attached_files:
            p = Path(path_str)
            is_img = p.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp")
            icon = "📷" if is_img else "📎"

            chip = tk.Frame(
                self._attach_frame, bg=C.GLASS_4, padx=8, pady=4,
                highlightthickness=1, highlightbackground=C.BLUE
            )
            chip.pack(side="left", padx=4, pady=2)

            tk.Label(
                chip, text=f"{icon} {p.name[:20]}",
                font=(F._FALLBACK, F.XS, "bold"),
                bg=C.GLASS_4, fg=C.FG_1
            ).pack(side="left", padx=(0, 6))

            del_lbl = tk.Label(
                chip, text="✕",
                font=(F._PRIMARY, F.XS, "bold"),
                bg=C.GLASS_4, fg=C.FG_3, cursor="hand2"
            )
            del_lbl.pack(side="left")
            del_lbl.bind("<ButtonRelease-1>", lambda e, ps=path_str: self.remove_attachment(ps))

    def _pick_files(self) -> None:
        try:
            from tkinter import filedialog
            paths = filedialog.askopenfilenames(
                title="Attach Files to HELIOS",
                filetypes=[("All Supported", "*.txt *.md *.py *.pdf *.docx *.json *.csv *.png *.jpg"), ("All Files", "*.*")]
            )
            if paths:
                for p in paths:
                    self.attach_file(p)
        except Exception:
            pass

    def _trigger_camera(self) -> None:
        """Launch ChatGPT-style in-app Camera Modal pop-up window."""
        try:
            from .camera_modal import CameraModal
            CameraModal(self._parent, on_capture=self.attach_file)
        except Exception as exc:
            # Fallback to file picker if camera modal fails
            self._pick_files()

    def _toggle_model_drawer(self) -> None:
        self._toggle_model_dropdown()

    def populate_voice_text(self, text: str) -> None:
        if text:
            self.set_text(text)

    def _submit(self) -> None:
        text = self.get_text()
        files = list(self._attached_files)
        self._attached_files.clear()
        self._render_attachment_chips()

        if text or files:
            self.clear()
            if self._on_send:
                import inspect
                try:
                    sig = inspect.signature(self._on_send)
                    if len(sig.parameters) >= 2:
                        self._on_send(text, files)
                    else:
                        self._on_send(text)
                except Exception:
                    self._on_send(text)

    def get_text(self) -> str:
        return self.entry.get().strip()

    def clear(self) -> None:
        self.entry.delete(0, tk.END)
        self.ph_label.place(x=8, y=6, relwidth=0.9, relheight=0.75)

    def set_text(self, text: str) -> None:
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)
        self.ph_label.place_forget()

    def focus(self) -> None:
        self.entry.focus_set()

    def set_active_model(self, model: str) -> None:
        self._active_model = model
        if not self._is_auto:
            self.model_lbl.configure(text=f"MODEL: {model.upper()} ▼")

    def update_context(self, model: str = None, mode: str = None) -> None:
        if model:
            self._active_model = model
        if mode:
            self._is_auto = (mode.upper() == "AUTO")
            lbl_text = "MODEL: AUTO ▼" if self._is_auto else f"MODEL: {self._active_model.upper()} ▼"
            self.model_lbl.configure(text=lbl_text, fg=C.BLUE_L if self._is_auto else C.OK)

    def _on_theme_changed(self) -> None:
        try:
            self.frame.configure(bg=C.BG)
            self.dock.configure(bg=C.GLASS_3, highlightbackground=C.GLASS_BD_3)
            self.row.configure(bg=C.GLASS_3)
            self.hl_line.configure(bg=C.GLASS_HL)
            self.entry_container.configure(bg=C.GLASS_1, highlightbackground=C.BORDER)
            self.entry.configure(bg=C.GLASS_1, fg=C.FG_1, insertbackground=C.BLUE)
            self.ph_label.configure(bg=C.GLASS_1, fg=C.FG_3)
            self.model_pill.configure(bg=C.GLASS_4, highlightbackground=C.GLASS_BD_4)
            self.model_lbl.configure(bg=C.GLASS_4)
        except Exception:
            pass
