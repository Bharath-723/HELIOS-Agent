"""
ui/chat_view.py — HELIOS v4.0 Chat View
=========================================
Premium information surface for human-AI conversation.

Message design:
  USER    — Right-aligned glass bubble (GLASS_3 + BLUE border)
            Hover reveals: Copy / Edit / Delete / Retry
  HELIOS  — Elevated glass response card (GLASS_3 surface)
            Left accent gradient strip, HELIOS badge, timestamp
            Hover reveals: Copy / Save / Regenerate
  ERROR   — Red-tinted glass card (ERR_CARD tokens)
            Error icon, concise explanation, recovery hint
  SYSTEM  — Centred inline notice (muted, no card chrome)

Interactions:
  • Smooth fade-in: opacity 0 → 1 over ~180ms (6 steps × 30ms)
  • Action buttons appear on card hover, disappear on leave
  • Email workflow triggered on template detection
  • Streaming placeholder updates text in-place
"""

from __future__ import annotations
import urllib.parse
import webbrowser
import tkinter as tk
from datetime import datetime
from pathlib import Path
from .theme import C, F, S, ThemeManager, hex_lerp
from .icon_manager import I
from .home_screen import HomeScreen
from .thinking_indicator import ThinkingIndicator


class ChatView:
    """Scrollable conversation feed — home screen, messages, errors, streaming."""

    def __init__(self, parent: tk.Widget, anim_engine=None,
                 on_home_action: callable = None,
                 on_trigger_file: callable = None,
                 on_drag_start: callable = None,
                 on_drag_do: callable = None) -> None:
        self._parent        = parent
        self._engine        = anim_engine
        self._on_home_action = on_home_action
        self._on_trigger_file = on_trigger_file
        self._on_drag_start  = on_drag_start
        self._on_drag_do     = on_drag_do

        self._think_w: ThinkingIndicator | None = None
        self._home_view: HomeScreen | None = None
        self._cards_registry: list[dict] = []

        # Container
        self.frame = tk.Frame(parent, bg=C.BG_S)
        self._build()

        # Debug mode: outline all regions with colored borders
        import os
        self._debug = os.environ.get("HELIOS_UI_DEBUG", "0") == "1"
        if self._debug:
            self.frame.configure(highlightthickness=2, highlightbackground="#FF0000")

        ThemeManager.add_listener(self._on_theme_changed)

    # ─────────────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # Scrollable canvas feed
        self.canvas = tk.Canvas(self.frame, bg=C.BG_S, highlightthickness=0, bd=0)
        self.vsb    = tk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")

        # Inner container frame
        self.msgs = tk.Frame(self.canvas, bg=C.BG_S)
        self._cw  = self.canvas.create_window((0, 0), window=self.msgs, anchor="nw")

        self.msgs.bind("<Configure>",
                       lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(self._cw, width=e.width))

        # Mouse wheel scrolling
        self._bind_scroll(self.msgs)
        self.canvas.bind("<MouseWheel>",
                         lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Drag bindings (for frameless window movement)
        if self._on_drag_start and self._on_drag_do:
            self.canvas.bind("<Button-1>",  self._on_drag_start)
            self.canvas.bind("<B1-Motion>", self._on_drag_do)
            self.msgs.bind("<Button-1>",    self._on_drag_start)
            self.msgs.bind("<B1-Motion>",   self._on_drag_do)

        # Default: show home screen
        self.show_home_screen()

    # ─────────────────────────────────────────────────────────────────────────
    def is_visible(self) -> bool:
        """Returns True only when the chat viewport is actually visible on screen.

        Checks: widget exists + is mapped + has non-zero dimensions.
        This is the correct invariant check — winfo_exists() alone is insufficient.
        """
        try:
            return (
                self.frame.winfo_exists() and
                self.frame.winfo_ismapped() and
                self.frame.winfo_width() > 0 and
                self.frame.winfo_height() > 0 and
                self.canvas.winfo_exists() and
                self.canvas.winfo_ismapped() and
                self.canvas.winfo_width() > 0 and
                self.canvas.winfo_height() > 0
            )
        except Exception:
            return False

    def _get_msg_width(self) -> int:
        """Compute dynamic message text width in characters based on actual canvas pixel width."""
        try:
            px = self.canvas.winfo_width()
            if px < 80:
                px = 500  # fallback before canvas is mapped
            # 1 char ≈ 8px at MD font size; subtract padding (28px left+right)
            return max(20, min(70, (px - 28) // 8))
        except Exception:
            return 40

    def _bind_scroll(self, w: tk.Widget) -> None:
        w.bind("<MouseWheel>",
               lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        for child in w.winfo_children():
            self._bind_scroll(child)

    # ─────────────────────────────────────────────────────────────────────────
    def show_home_screen(self) -> None:
        self.clear()
        self._home_view = HomeScreen(
            self.msgs,
            on_action=self._on_home_action,
            on_load_session=self.load_session_direct,
            on_trigger_file=self._on_trigger_file,
        )
        self._home_view.frame.pack(fill="both", expand=True)
        self._bind_scroll(self._home_view.frame)

        if self._on_drag_start and self._on_drag_do:
            for w in (
                self._home_view.frame,
                self._home_view.container,
                self._home_view.greeting_lbl,
                self._home_view.sub_lbl,
            ):
                w.bind("<Button-1>",  self._on_drag_start)
                w.bind("<B1-Motion>", self._on_drag_do)

        self._fade_in_widget(self._home_view.frame, C.BG_S, C.FG_1, steps=6)

    def hide_home_screen(self) -> None:
        if self._home_view:
            self._home_view.frame.pack_forget()
            self._home_view = None

    def load_session_direct(self, session_id: str) -> None:
        root = self.frame.winfo_toplevel()
        root.event_generate("<<LoadSession>>", data=session_id)

    # ═════════════════════════════════════════════════════════════════════════
    # USER MESSAGES  —— right-aligned premium glass bubble (3-layer depth)
    # ═════════════════════════════════════════════════════════════════════════
    def add_user_message(self, text: str, attachments: list = None) -> None:
        self.hide_home_screen()

        outer = tk.Frame(self.msgs, bg=C.BG_S)
        outer.pack(fill="x", padx=14, pady=(S.MSG_GAP, 0))

        # ── Attachment chips ────────────────────────────────────────────────────────────────
        if attachments:
            chip_row = tk.Frame(outer, bg=C.BG_S)
            chip_row.pack(anchor="e", pady=(0, 4))
            for path in attachments:
                name = Path(path).name
                ext = Path(path).suffix.lower()
                if ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
                    try:
                        from PIL import Image, ImageTk
                        img = Image.open(path)
                        img.thumbnail((240, 180))
                        photo = ImageTk.PhotoImage(img)
                        img_lbl = tk.Label(chip_row, image=photo, bg=C.BG_S)
                        img_lbl.image = photo
                        img_lbl.pack(anchor="e", pady=(2, 4))
                    except Exception:
                        pass
                chip = tk.Label(chip_row,
                                 text=f"  {I.FILE_DOC}  {name}  ",
                                 font=(F._FALLBACK, F.XS),
                                 bg=C.CHIP_BG, fg=C.CHIP_FG,
                                 padx=4, pady=2)
                chip.pack(side="left", padx=2)

        # ── Layer 1: Shadow frame (simulated elevation) ──────────────────────────
        shadow = tk.Frame(outer, bg=C.SHADOW_SM)
        shadow.pack(anchor="e")

        # ── Layer 2: Glass surface with border ────────────────────────────────
        bubble = tk.Frame(shadow,
                           bg=C.USER_BG,
                           highlightthickness=1,
                           highlightbackground=C.USER_BORDER)
        bubble.pack(fill="both", expand=True, padx=(0, 1), pady=(0, 1))

        # ── Layer 3: Top highlight (glass top-edge light) ─────────────────────
        tk.Frame(bubble, bg=C.USER_BORDER, height=1).pack(fill="x")

        inner = tk.Frame(bubble, bg=C.USER_BG, padx=12, pady=8)
        inner.pack()

        # ── "You" label ────────────────────────────────────────────────────────────────────
        you_row = tk.Frame(inner, bg=C.USER_BG)
        you_row.pack(fill="x", pady=(0, 4))
        tk.Label(you_row, text="You",
                 font=(F._PRIMARY, F.XS, "bold"),
                 bg=C.USER_BG, fg=C.BLUE_L).pack(side="left")

        # ── Message text (responsive width) ──────────────────────────────────────
        max_w      = self._get_msg_width()
        calc_width = max(4, min(len(text.strip()) + 3, max_w)) if "\n" not in text else max_w
        lines = self._estimate_lines(text, calc_width)
        txt = tk.Text(inner,
                       font=(F._FALLBACK, F.MD),
                       bg=C.USER_BG, fg=C.FG_USER,
                       relief="flat", bd=0,
                       wrap="word", width=calc_width, height=lines,
                       cursor="xterm", exportselection=True)
        txt.insert("1.0", text)
        txt.configure(state="disabled")
        txt.pack()

        # ── Hover action bar ────────────────────────────────────────────────────────
        action_bar = tk.Frame(outer, bg=C.BG_S)
        self._make_action_btn(action_bar, I.COPY   + " Copy",
                               lambda: self._copy_text(text), bg=C.BG_S)
        self._make_action_btn(action_bar, I.EDIT   + " Edit",
                               lambda: self._edit_user_text(text), bg=C.BG_S)
        def _delete_card():
            outer.destroy()
            self.hide_thinking()
            try:
                self.frame.winfo_toplevel().event_generate("<<MessageDeleted>>")
            except Exception:
                pass

        self._make_action_btn(action_bar, I.DELETE + " Delete", _delete_card, bg=C.BG_S)

        def _on_hover_in(e=None):
            try:
                bg_elevated = C.USER_BG2 if hasattr(C, 'USER_BG2') else "#1B3270"
                bubble.configure(bg=bg_elevated, highlightbackground=C.BLUE)
                inner.configure(bg=bg_elevated)
                you_row.configure(bg=bg_elevated)
                txt.configure(bg=bg_elevated)
                for child in you_row.winfo_children():
                    child.configure(bg=bg_elevated)
                action_bar.pack(anchor="e", pady=(2, 0))
            except Exception:
                pass

        def _on_hover_out(e=None):
            try:
                bubble.configure(bg=C.USER_BG, highlightbackground=C.USER_BORDER)
                inner.configure(bg=C.USER_BG)
                you_row.configure(bg=C.USER_BG)
                txt.configure(bg=C.USER_BG)
                for child in you_row.winfo_children():
                    child.configure(bg=C.USER_BG)
                action_bar.pack_forget()
            except Exception:
                pass

        def _check_leave(e):
            try:
                rx, ry = outer.winfo_pointerx(), outer.winfo_pointery()
                x1, y1 = outer.winfo_rootx(), outer.winfo_rooty()
                x2, y2 = x1 + outer.winfo_width(), y1 + outer.winfo_height()
                if not (x1 <= rx <= x2 and y1 <= ry <= y2):
                    _on_hover_out()
            except Exception:
                _on_hover_out()

        for w in (outer, shadow, bubble, inner, txt, you_row):
            w.bind("<Enter>", _on_hover_in)
            w.bind("<Leave>", lambda e: self.frame.after(60, lambda: _check_leave(e)))

        # Messages appear immediately — no fade delay on critical render path
        self._bind_scroll(outer)
        self._scroll_to_bottom(force=True)

    # ═══════════════════════════════════════════════════════════════════════
    # ASSISTANT RESPONSE CARDS  —— elevated glass surface (DEPTH_2), 3-layer
    # ═══════════════════════════════════════════════════════════════════════
    def add_helios_message(self, text: str, metadata: dict = None) -> tk.Frame:
        self.hide_home_screen()
        if metadata is None:
            metadata = {}
        ts = datetime.now().strftime("%I:%M %p")

        outer = tk.Frame(self.msgs, bg=C.BG_S)
        outer.pack(fill="x", padx=14, pady=(S.MSG_GAP, 0))

        # Layer 1: shadow (elevation illusion)
        shadow = tk.Frame(outer, bg=C.SHADOW_SM)
        shadow.pack(anchor="w", fill="x")

        # Layer 2: glass surface
        card = tk.Frame(shadow,
                         bg=C.DEPTH_2,
                         highlightthickness=1,
                         highlightbackground=C.DEPTH_BD_2)
        card.pack(fill="both", expand=True, padx=(0, 1), pady=(0, 1))

        # Layer 3: top highlight (glass top-edge light)
        tk.Frame(card, bg=C.DEPTH_BD_3, height=1).pack(fill="x")

        row = tk.Frame(card, bg=C.DEPTH_2)
        row.pack(fill="both", expand=True)

        # Blue accent strip
        accent = tk.Frame(row, bg=C.BLUE, width=3)
        accent.pack(side="left", fill="y")

        body = tk.Frame(row, bg=C.DEPTH_2)
        body.pack(side="left", fill="both", expand=True)

        # ── Header row ────────────────────────────────────────────────────
        hdr = tk.Frame(body, bg=C.DEPTH_2)
        hdr.pack(fill="x", padx=12, pady=(8, 4))

        lbl_h = tk.Label(hdr, text="✦ HELIOS",
                          font=(F._PRIMARY, F.SM, "bold"),
                          bg=C.DEPTH_2, fg=C.FG_1)
        lbl_h.pack(side="left")

        model_name = metadata.get("model", "")
        if model_name:
            chip = tk.Label(hdr, text=f"  {model_name}  ",
                             font=(F._FALLBACK, F.XS),
                             bg=C.CHIP_BG, fg=C.CHIP_FG,
                             padx=2, pady=1)
            chip.pack(side="left", padx=(8, 0))

        lbl_t = tk.Label(hdr, text=ts,
                          font=(F._FALLBACK, F.XS),
                          bg=C.DEPTH_2, fg=C.FG_3)
        lbl_t.pack(side="right")

        # ── Message body (responsive width) ─────────────────────────────
        msg_w = self._get_msg_width()
        lines = self._estimate_lines(text, msg_w)
        txt = tk.Text(body,
                       font=(F._FALLBACK, F.MD),
                       bg=C.DEPTH_2, fg=C.FG_HELIOS,
                       relief="flat", bd=0,
                       padx=12, pady=4,
                       wrap="word", width=msg_w, height=lines,
                       cursor="xterm")
        self._render_markdown_content(txt, text)
        txt.pack(fill="x")

        # ── Footer ────────────────────────────────────────────────────────
        footer = tk.Frame(body, bg=C.DEPTH_2)
        footer.pack(fill="x", padx=12, pady=(2, 6))

        meta_text = f"● {model_name}" if model_name else ""
        lbl_m = tk.Label(footer, text=meta_text,
                          font=(F._FALLBACK, F.XS),
                          bg=C.DEPTH_2, fg=C.FG_3)
        lbl_m.pack(side="left")

        if self._is_email_template(text):
            self._build_email_actions(body, text)

        # ── Hover action bar ──────────────────────────────────────────────
        action_bar = tk.Frame(body, bg=C.DEPTH_2)
        self._make_action_btn(action_bar, I.COPY  + " Copy",
                               lambda: self._copy_text(text),  bg=C.DEPTH_2)
        self._make_action_btn(action_bar, I.SAVE  + " Save",
                               lambda: self._save_note(text),  bg=C.DEPTH_2)
        self._make_action_btn(action_bar, I.RETRY + " Regen",
                               lambda: self._regenerate_message(), bg=C.DEPTH_2)

        def _enter(e):
            action_bar.pack(anchor="e", padx=12, pady=(0, 6))
            card.configure(highlightbackground=C.BLUE)
        def _leave(e):
            action_bar.pack_forget()
            card.configure(highlightbackground=C.DEPTH_BD_2)

        card.bind("<Enter>", _enter)
        card.bind("<Leave>", _leave)

        self._cards_registry.append({
            "outer": outer, "card": card, "accent": accent, "body": body,
            "hdr": hdr, "lbl_h": lbl_h, "lbl_t": lbl_t, "txt": txt,
            "footer": footer, "lbl_m": lbl_m, "action_bar": action_bar,
            "type": "assistant", "text_content": text,
        })

        self._bind_scroll(outer)
        self._scroll_to_bottom()
        return card


    # ═════════════════════════════════════════════════════════════════════════
    # STREAMING PLACEHOLDER
    # ═════════════════════════════════════════════════════════════════════════
    def add_streaming_helios_message(self, metadata: dict = None) -> tuple:
        self.hide_home_screen()
        if metadata is None:
            metadata = {}
        ts = datetime.now().strftime("%I:%M %p")

        outer = tk.Frame(self.msgs, bg=C.BG_S)
        outer.pack(fill="x", padx=14, pady=(S.MSG_GAP, 0))

        shadow = tk.Frame(outer, bg=C.SHADOW_SM)
        shadow.pack(anchor="w", fill="x")

        card = tk.Frame(shadow,
                         bg=C.DEPTH_2,
                         highlightthickness=1,
                         highlightbackground=C.DEPTH_BD_2)
        card.pack(fill="both", expand=True, padx=(0,1), pady=(0,1))

        tk.Frame(card, bg=C.DEPTH_BD_3, height=1).pack(fill="x")

        row = tk.Frame(card, bg=C.DEPTH_2)
        row.pack(fill="both", expand=True)

        # Cyan accent strip (streaming = active generation)
        accent = tk.Frame(row, bg=C.CYAN, width=3)
        accent.pack(side="left", fill="y")

        body = tk.Frame(row, bg=C.DEPTH_2)
        body.pack(side="left", fill="both", expand=True)

        hdr = tk.Frame(body, bg=C.DEPTH_2)
        hdr.pack(fill="x", padx=12, pady=(8, 4))

        lbl_h = tk.Label(hdr, text="H  HELIOS",
                          font=(F._PRIMARY, F.SM, "bold"),
                          bg=C.DEPTH_2, fg=C.FG_1)
        lbl_h.pack(side="left")

        stream_dot = tk.Label(hdr, text="◉",
                              font=(F._FALLBACK, F.XS),
                              bg=C.DEPTH_2, fg=C.CYAN)
        stream_dot.pack(side="left", padx=(8, 0))

        lbl_t = tk.Label(hdr, text=ts,
                          font=(F._FALLBACK, F.XS),
                          bg=C.DEPTH_2, fg=C.FG_3)
        lbl_t.pack(side="right")

        msg_w = self._get_msg_width()
        txt = tk.Text(body,
                       font=(F._FALLBACK, F.MD),
                       bg=C.DEPTH_2, fg=C.FG_HELIOS,
                       relief="flat", bd=0,
                       padx=12, pady=4,
                       wrap="word", width=msg_w, height=1,
                       cursor="xterm")
        txt.configure(state="disabled")
        txt.pack(fill="x")

        footer = tk.Frame(body, bg=C.DEPTH_2)
        footer.pack(fill="x", padx=12, pady=(2, 6))

        lbl_m = tk.Label(footer, text="Generating···",
                          font=(F._FALLBACK, F.XS),
                          bg=C.DEPTH_2, fg=C.FG_3)
        lbl_m.pack(side="left")

        reg = {
            "outer": outer, "card": card, "accent": accent, "body": body,
            "hdr": hdr, "lbl_h": lbl_h, "lbl_t": lbl_t, "txt": txt,
            "footer": footer, "lbl_m": lbl_m,
            "type": "streaming", "text_content": "",
        }
        self._cards_registry.append(reg)

        self._bind_scroll(outer)
        self._scroll_to_bottom()
        return card, txt, lbl_m

    def _render_markdown_content(self, txt_widget: tk.Text, raw_text: str) -> None:
        txt_widget.configure(state="normal")
        txt_widget.delete("1.0", tk.END)

        txt_widget.tag_configure("bold", font=(F._FALLBACK, F.MD, "bold"), foreground=C.FG_1)
        txt_widget.tag_configure("italic", font=(F._FALLBACK, F.MD, "italic"), foreground=C.FG_2)
        txt_widget.tag_configure("underline", font=(F._FALLBACK, F.MD, "underline"), foreground=C.FG_1)
        txt_widget.tag_configure("bullet", lmargin1=12, lmargin2=24)

        clean_text = raw_text
        if "(via " in clean_text and clean_text.rstrip().endswith(")"):
            clean_text = clean_text.rstrip().rsplit("(via ", 1)[0].rstrip()

        lines = clean_text.splitlines()
        import re
        for line_idx, line in enumerate(lines):
            if line_idx > 0:
                txt_widget.insert(tk.END, "\n")

            is_bullet = False
            clean_line = line
            strip_line = clean_line.strip()
            if strip_line.startswith("* ") or strip_line.startswith("- ") or strip_line.startswith("• "):
                is_bullet = True
                content_part = strip_line[2:].strip()
                clean_line = f"  • {content_part}"

            tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*|<u>.*?</u>)', clean_line)
            for token in tokens:
                if not token:
                    continue
                if token.startswith("**") and token.endswith("**") and len(token) >= 4:
                    tags = ("bold", "bullet") if is_bullet else ("bold",)
                    txt_widget.insert(tk.END, token[2:-2], tags)
                elif token.startswith("*") and token.endswith("*") and len(token) >= 2 and not token.startswith("**"):
                    tags = ("italic", "bullet") if is_bullet else ("italic",)
                    txt_widget.insert(tk.END, token[1:-1], tags)
                elif token.startswith("<u>") and token.endswith("</u>") and len(token) >= 7:
                    tags = ("underline", "bullet") if is_bullet else ("underline",)
                    txt_widget.insert(tk.END, token[3:-4], tags)
                else:
                    tags = ("bullet",) if is_bullet else ()
                    txt_widget.insert(tk.END, token, tags)

        txt_widget.configure(state="disabled")

    def update_streaming_content(self, txt: tk.Text, lbl_m: tk.Label,
                                  text: str, metadata: dict = None) -> None:
        msg_w = self._get_msg_width()
        self._render_markdown_content(txt, text)
        lines = self._estimate_lines(text, msg_w)
        txt.configure(height=lines, state="disabled")

        if metadata:
            model = metadata.get("model", "")
            meta_txt = f"● {model}" if model else ""
            lbl_m.configure(text=meta_txt)
        self._scroll_to_bottom()

    # ═════════════════════════════════════════════════════════════════════════
    # PREMIUM ERROR CARDS  ── red-tinted glass
    # ═════════════════════════════════════════════════════════════════════════
    def add_error_card(self, title: str, desc: str, recovery: str = "") -> None:
        self.hide_home_screen()

        outer = tk.Frame(self.msgs, bg=C.BG_S)
        outer.pack(fill="x", padx=14, pady=8)

        # Red-tinted glass card
        card = tk.Frame(outer,
                         bg=C.ERR_CARD_BG,
                         highlightthickness=1,
                         highlightbackground=C.ERR_CARD_BD)
        card.pack(fill="x")

        # Left red accent strip
        accent = tk.Frame(card, bg=C.ERR, width=3)
        accent.pack(side="left", fill="y")

        body = tk.Frame(card, bg=C.ERR_CARD_BG, padx=14, pady=10)
        body.pack(side="left", fill="both", expand=True)

        # Error header: icon + title
        hdr_row = tk.Frame(body, bg=C.ERR_CARD_BG)
        hdr_row.pack(anchor="w")

        tk.Label(hdr_row, text=I.ERR_ICON + "  " + title,
                  font=(F._PRIMARY, F.MD, "bold"),
                  bg=C.ERR_CARD_BG, fg=C.ERR_CARD_FG).pack(side="left")

        # Description
        tk.Label(body, text=desc,
                  font=(F._FALLBACK, F.SM),
                  bg=C.ERR_CARD_BG, fg=C.FG_2,
                  wraplength=340, justify="left").pack(anchor="w", pady=(6, 0))

        # Recovery suggestion
        if recovery:
            tk.Label(body, text=f"  Suggestion:  {recovery}",
                      font=(F._FALLBACK, F.XS, "bold"),
                      bg=C.ERR_CARD_BG, fg=C.WARN_L,
                      wraplength=340, justify="left").pack(anchor="w", pady=(6, 0))

        self._fade_in_widget(card, C.ERR_CARD_BG, C.ERR_CARD_FG)
        self._bind_scroll(outer)
        self._scroll_to_bottom(force=True)

    # ═════════════════════════════════════════════════════════════════════════
    # FADE-IN ANIMATION
    # ═════════════════════════════════════════════════════════════════════════
    def _fade_in_widget(self, w: tk.Widget, target_bg: str, target_fg: str,
                         steps: int = 1, step: int = 1) -> None:
        """Instant crisp render — sets target colors immediately with zero dark text delay."""
        if not w.winfo_exists():
            return
        try:
            w.configure(bg=target_bg)
            if isinstance(w, (tk.Label, tk.Button, tk.Text)):
                w.configure(fg=target_fg)
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════════════════════
    # SYSTEM NOTICES
    # ═════════════════════════════════════════════════════════════════════════
    def add_system_notice(self, text: str) -> None:
        row = tk.Frame(self.msgs, bg=C.BG_S)
        row.pack(fill="x", pady=4)

        fg = (C.WARN if "warn" in text.lower()
              else C.OK if ("success" in text.lower() or "started" in text.lower())
              else C.FG_3)

        lbl = tk.Label(row, text=text,
                        font=(F._FALLBACK, F.XS),
                        bg=C.BG_S, fg=fg)
        lbl.pack()

        self._fade_in_widget(lbl, C.BG_S, fg)
        self._bind_scroll(row)
        self._scroll_to_bottom()

    # ═════════════════════════════════════════════════════════════════════════
    # EMAIL WORKFLOW
    # ═════════════════════════════════════════════════════════════════════════
    def _is_email_template(self, text: str) -> bool:
        keywords = ["subject:", "dear", "to:", "from:", "regards", "sincerely", "email draft"]
        return sum(1 for kw in keywords if kw in text.lower()) >= 2

    def _build_email_actions(self, parent: tk.Widget, body_text: str) -> None:
        row = tk.Frame(parent, bg=C.GLASS_3, padx=4, pady=4)
        row.pack(fill="x", padx=12, pady=4)
        self._make_action_btn(row, "  Send Email  ",
                               lambda: self._trigger_email_workflow(body_text),
                               bg=C.GLASS_3)

    def _trigger_email_workflow(self, body_text: str) -> None:
        modal = tk.Toplevel(self.frame)
        modal.overrideredirect(True)
        modal.attributes("-topmost", True)
        modal.configure(bg=C.GLASS_4)

        root = self.frame.winfo_toplevel()
        rx, ry = root.winfo_rootx(), root.winfo_rooty()
        modal.geometry(f"320x180+{rx + 50}+{ry + 200}")

        tk.Label(modal, text="Recipient Email Address:",
                  font=(F._PRIMARY, F.XS, "bold"), bg=C.GLASS_4, fg=C.FG_1
                  ).pack(anchor="w", padx=12, pady=(12, 2))
        rec_ent = tk.Entry(modal, font=(F._FALLBACK, F.SM),
                            bg=C.BG_INPUT, fg=C.FG_1, relief="flat", bd=4)
        rec_ent.pack(fill="x", padx=12, pady=2)
        rec_ent.focus_set()

        tk.Label(modal, text="Subject:",
                  font=(F._PRIMARY, F.XS, "bold"), bg=C.GLASS_4, fg=C.FG_1
                  ).pack(anchor="w", padx=12, pady=(6, 2))
        sub_ent = tk.Entry(modal, font=(F._FALLBACK, F.SM),
                            bg=C.BG_INPUT, fg=C.FG_1, relief="flat", bd=4)
        sub_ent.insert(0, "Drafted by HELIOS")
        sub_ent.pack(fill="x", padx=12, pady=2)

        def proceed():
            recipient = rec_ent.get().strip()
            subject   = sub_ent.get().strip()
            modal.destroy()
            body_esc = urllib.parse.quote(body_text)
            sub_esc  = urllib.parse.quote(subject)
            webbrowser.open(f"mailto:{recipient}?subject={sub_esc}&body={body_esc}")

        btn_row = tk.Frame(modal, bg=C.GLASS_4)
        btn_row.pack(fill="x", padx=12, pady=12)

        tk.Button(btn_row, text="Open Mail Client",
                   font=(F._FALLBACK, F.XS), bg=C.BLUE, fg="white",
                   command=proceed).pack(side="right")
        tk.Button(btn_row, text="Cancel",
                   font=(F._FALLBACK, F.XS), bg=C.BORDER, fg=C.FG_2,
                   command=modal.destroy).pack(side="right", padx=6)

    # ═════════════════════════════════════════════════════════════════════════
    # ACTION BUTTONS
    # ═════════════════════════════════════════════════════════════════════════
    def _make_action_btn(self, parent: tk.Widget, label: str,
                          command: callable, bg: str = None) -> tk.Label:
        """Create a small inline action button (hover to reveal)."""
        card_bg = bg or C.GLASS_3
        lbl = tk.Label(parent, text=label,
                        font=(F._FALLBACK, F.XS),
                        bg=card_bg, fg=C.FG_3,
                        cursor="hand2", padx=6, pady=3)
        lbl.pack(side="left", padx=2)

        def _enter(e): lbl.configure(fg=C.BLUE)
        def _leave(e): lbl.configure(fg=C.FG_3)

        lbl.bind("<Enter>",           _enter)
        lbl.bind("<Leave>",           _leave)
        lbl.bind("<ButtonRelease-1>", lambda e: command())
        return lbl

    # Keep old name for backward compatibility
    def _add_action_btn(self, parent: tk.Widget, label: str, command: callable) -> tk.Label:
        return self._make_action_btn(parent, label, command)

    # ─────────────────────────────────────────────────────────────────────────
    def _copy_text(self, text: str) -> None:
        self.frame.clipboard_clear()
        self.frame.clipboard_append(text)
        self.add_system_notice("Copied to clipboard.")

    def _edit_user_text(self, text: str) -> None:
        self._last_edit_text = text
        try:
            self._copy_text(text)
        except Exception:
            pass
        self.frame.winfo_toplevel().event_generate("<<EditUserText>>")

    def _save_note(self, text: str) -> None:
        self.frame.winfo_toplevel().event_generate("<<SaveNote>>", data=text)

    def _regenerate_message(self) -> None:
        self.frame.winfo_toplevel().event_generate("<<Regenerate>>")

    # ═════════════════════════════════════════════════════════════════════════
    # THINKING INDICATOR
    # ═════════════════════════════════════════════════════════════════════════
    def show_thinking(self) -> ThinkingIndicator:
        self.hide_thinking()
        self._think_w = ThinkingIndicator(self.msgs, self._engine)
        self._scroll_to_bottom()
        return self._think_w

    def hide_thinking(self) -> None:
        if self._think_w:
            self._think_w.destroy()
            self._think_w = None

    # ═════════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═════════════════════════════════════════════════════════════════════════
    def _estimate_lines(self, text: str, chars_per_line: int) -> int:
        lines = 0
        for para in text.split("\n"):
            lines += max(1, -(-len(para) // chars_per_line))
        return max(1, min(lines, 40))

    def _scroll_to_bottom(self, force: bool = False) -> None:
        def _do():
            if not self.canvas.winfo_exists():
                return
            if force:
                self.canvas.yview_moveto(1.0)
                return
            try:
                _, bottom = self.canvas.yview()
                if bottom >= 0.94 or 1.0 - bottom < 0.06:
                    self.canvas.yview_moveto(1.0)
            except Exception:
                self.canvas.yview_moveto(1.0)
        self.canvas.after(50, _do)

    def clear(self) -> None:
        for w in self.msgs.winfo_children():
            w.destroy()
        self._cards_registry.clear()
        self._think_w = None

    # ═════════════════════════════════════════════════════════════════════════
    # LOAD SESSION
    # ═════════════════════════════════════════════════════════════════════════
    def load_session_direct(self, session_id: str) -> None:
        root = self.frame.winfo_toplevel()
        root.event_generate("<<LoadSession>>", data=session_id)

    # ─────────────────────────────────────────────────────────────────────────
    def _on_theme_changed(self) -> None:
        try:
            self.frame.configure(bg=C.BG_S)
            self.canvas.configure(bg=C.BG_S)
            self.msgs.configure(bg=C.BG_S)

            for entry in self._cards_registry:
                try:
                    if entry.get("type") in ("assistant", "streaming"):
                        if "outer" in entry and entry["outer"].winfo_exists(): entry["outer"].configure(bg=C.BG_S)
                        if "card" in entry and entry["card"].winfo_exists(): entry["card"].configure(bg=C.GLASS_3, highlightbackground=C.GLASS_BD_3)
                        if "accent" in entry and entry["accent"].winfo_exists(): entry["accent"].configure(bg=C.BLUE)
                        if "body" in entry and entry["body"].winfo_exists(): entry["body"].configure(bg=C.GLASS_3)
                        if "hdr" in entry and entry["hdr"].winfo_exists(): entry["hdr"].configure(bg=C.GLASS_3)
                        if "lbl_h" in entry and entry["lbl_h"].winfo_exists(): entry["lbl_h"].configure(bg=C.GLASS_3, fg=C.FG_1)
                        if "lbl_t" in entry and entry["lbl_t"].winfo_exists(): entry["lbl_t"].configure(bg=C.GLASS_3, fg=C.FG_3)
                        if "txt" in entry and entry["txt"].winfo_exists(): entry["txt"].configure(bg=C.GLASS_3, fg=C.FG_HELIOS)
                        if "footer" in entry and entry["footer"].winfo_exists(): entry["footer"].configure(bg=C.GLASS_3)
                        if "lbl_m" in entry and entry["lbl_m"].winfo_exists(): entry["lbl_m"].configure(bg=C.GLASS_3, fg=C.FG_3)
                        if "action_bar" in entry and entry["action_bar"].winfo_exists():
                            entry["action_bar"].configure(bg=C.GLASS_3)
                            for child in entry["action_bar"].winfo_children():
                                if child.winfo_exists():
                                    child.configure(bg=C.GLASS_3, fg=C.FG_3)
                except Exception:
                    pass
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════════════════════
    # RAZORPAY AGENTIC PAYMENT CARDS
    # ═════════════════════════════════════════════════════════════════════════
    def add_payment_transaction_card(self, intent_dict: dict, on_authorize: callable, on_cancel: callable) -> tk.Frame:
        self.hide_home_screen()
        ts = datetime.now().strftime("%I:%M %p")

        outer = tk.Frame(self.msgs, bg=C.BG_S)
        outer.pack(fill="x", padx=14, pady=(S.MSG_GAP, 0))

        card = tk.Frame(outer,
                        bg=C.GLASS_3,
                        highlightthickness=2,
                        highlightbackground=C.GOLD if hasattr(C, 'GOLD') else "#F59E0B")
        card.pack(anchor="w", fill="x")

        accent = tk.Frame(card, bg=C.GOLD if hasattr(C, 'GOLD') else "#F59E0B", width=4)
        accent.pack(side="left", fill="y")

        body = tk.Frame(card, bg=C.GLASS_3, padx=14, pady=10)
        body.pack(side="left", fill="both", expand=True)

        hdr = tk.Frame(body, bg=C.GLASS_3)
        hdr.pack(fill="x", pady=(0, 6))

        tk.Label(hdr, text="💳 PAYMENT READY", font=(F._PRIMARY, F.MD, "bold"),
                 bg=C.GLASS_3, fg=C.FG_1).pack(side="left")
        
        tk.Label(hdr, text="  Razorpay Sandbox  ", font=(F._FALLBACK, F.XS, "bold"),
                 bg="#1E293B", fg="#38BDF8", padx=4, pady=1).pack(side="left", padx=8)

        tk.Label(hdr, text=ts, font=(F._FALLBACK, F.XS),
                 bg=C.GLASS_3, fg=C.FG_3).pack(side="right")

        grid = tk.Frame(body, bg=C.GLASS_3)
        grid.pack(fill="x", pady=6)

        amt_inr = intent_dict.get("amount", 0) / 100.0
        merchant = intent_dict.get("merchant_name", "Merchant")
        desc = intent_dict.get("description", "Product/Service")

        def _row(parent, label, val, is_bold=False, val_color=C.FG_1):
            rf = tk.Frame(parent, bg=C.GLASS_3)
            rf.pack(fill="x", pady=2)
            tk.Label(rf, text=label, font=(F._FALLBACK, F.SM), bg=C.GLASS_3, fg=C.FG_3, width=12, anchor="w").pack(side="left")
            font_spec = (F._PRIMARY, F.MD, "bold") if is_bold else (F._FALLBACK, F.SM)
            tk.Label(rf, text=val, font=font_spec, bg=C.GLASS_3, fg=val_color, anchor="w").pack(side="left")

        _row(grid, "Merchant:", merchant)
        _row(grid, "Item:", desc)
        _row(grid, "Amount:", f"₹{amt_inr:,.2f}", is_bold=True, val_color=C.CYAN)
        _row(grid, "Reason:", "Matches your request")
        
        lbl_status = tk.Label(body, text="Status: Awaiting your explicit authorization", font=(F._FALLBACK, F.XS, "bold"),
                              bg=C.GLASS_3, fg=C.GOLD if hasattr(C, 'GOLD') else "#F59E0B")
        lbl_status.pack(anchor="w", pady=(4, 8))

        ctrl = tk.Frame(body, bg=C.GLASS_3)
        ctrl.pack(fill="x", pady=(4, 0))

        intent_id = intent_dict.get("intent_id", "")

        def _do_cancel():
            btn_cancel.config(state="disabled")
            btn_auth.config(state="disabled")
            lbl_status.config(text="Status: Cancelled by user", fg=C.ERR_L if hasattr(C, 'ERR_L') else "#EF4444")
            on_cancel(intent_id)

        def _do_auth():
            btn_cancel.config(state="disabled")
            btn_auth.config(state="disabled")
            lbl_status.config(text="Status: Authorized — preparing Razorpay Order...", fg=C.OK_L if hasattr(C, 'OK_L') else "#10B981")
            on_authorize(intent_id)

        btn_cancel = tk.Button(ctrl, text="❌ Cancel", font=(F._FALLBACK, F.SM),
                               bg=C.BG_C2, fg=C.FG_1, activebackground=C.BG_S, activeforeground=C.FG_1,
                               relief="flat", bd=0, padx=12, pady=5, cursor="hand2", command=_do_cancel)
        btn_cancel.pack(side="left", padx=(0, 8))

        btn_auth = tk.Button(ctrl, text="💳 Authorize Payment", font=(F._PRIMARY, F.SM, "bold"),
                            bg=C.BLUE, fg="white", activebackground=C.BLUE_L, activeforeground="white",
                            relief="flat", bd=0, padx=16, pady=5, cursor="hand2", command=_do_auth)
        btn_auth.pack(side="left")

        self._bind_scroll(outer)
        self._scroll_to_bottom(force=True)
        return outer

    def add_payment_result_card(self, result_dict: dict) -> tk.Frame:
        self.hide_home_screen()
        ts = datetime.now().strftime("%I:%M %p")

        outer = tk.Frame(self.msgs, bg=C.BG_S)
        outer.pack(fill="x", padx=14, pady=(S.MSG_GAP, 0))

        success = result_dict.get("success", False)
        fg_accent = C.OK_L if success else (C.ERR_L if hasattr(C, 'ERR_L') else "#EF4444")
        title = "✓ PAYMENT COMPLETED & VERIFIED" if success else "⚠ PAYMENT VERIFICATION FAILED"

        card = tk.Frame(outer, bg=C.GLASS_3, highlightthickness=1, highlightbackground=fg_accent)
        card.pack(anchor="w", fill="x")

        accent = tk.Frame(card, bg=fg_accent, width=4)
        accent.pack(side="left", fill="y")

        body = tk.Frame(card, bg=C.GLASS_3, padx=14, pady=10)
        body.pack(side="left", fill="both", expand=True)

        hdr = tk.Frame(body, bg=C.GLASS_3)
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text=title, font=(F._PRIMARY, F.SM, "bold"), bg=C.GLASS_3, fg=fg_accent).pack(side="left")
        tk.Label(hdr, text=ts, font=(F._FALLBACK, F.XS), bg=C.GLASS_3, fg=C.FG_3).pack(side="right")

        if success:
            pid = result_dict.get("payment_id", "pay_••••1234")
            masked_pid = pid[:5] + "••••" + pid[-4:] if len(pid) > 9 else pid
            amt = result_dict.get("amount", 0) / 100.0
            
            tk.Label(body, text=f"Amount Verified: ₹{amt:,.2f}", font=(F._PRIMARY, F.MD, "bold"), bg=C.GLASS_3, fg=C.FG_1).pack(anchor="w", pady=2)
            tk.Label(body, text=f"Payment ID: {masked_pid}  |  HMAC Signature: Verified (Timing-Safe)", font=(F._FALLBACK, F.XS), bg=C.GLASS_3, fg=C.FG_3).pack(anchor="w")
        else:
            reason = result_dict.get("failure_reason", result_dict.get("message", "Verification check failed"))
            tk.Label(body, text=f"Reason: {reason}", font=(F._FALLBACK, F.SM), bg=C.GLASS_3, fg=fg_accent).pack(anchor="w", pady=2)
            tk.Label(body, text="Action: No funds were captured. Payment marked as unverified.", font=(F._FALLBACK, F.XS), bg=C.GLASS_3, fg=C.FG_3).pack(anchor="w")

        self._bind_scroll(outer)
        self._scroll_to_bottom(force=True)
        return outer

    # ═════════════════════════════════════════════════════════════════════════
    # CLOUD SCREEN PERMISSION CARD
    # ═════════════════════════════════════════════════════════════════════════
    def add_screen_permission_card(self, payload_dict: dict, on_decision: callable) -> tk.Frame:
        self.hide_home_screen()
        ts = datetime.now().strftime("%I:%M %p")

        outer = tk.Frame(self.msgs, bg=C.BG_S)
        outer.pack(fill="x", padx=14, pady=(S.MSG_GAP, 0))

        card = tk.Frame(outer,
                        bg=C.GLASS_3,
                        highlightthickness=2,
                        highlightbackground=C.BLUE if hasattr(C, 'BLUE') else "#3B82F6")
        card.pack(anchor="w", fill="x")

        accent = tk.Frame(card, bg=C.BLUE if hasattr(C, 'BLUE') else "#3B82F6", width=4)
        accent.pack(side="left", fill="y")

        body = tk.Frame(card, bg=C.GLASS_3, padx=14, pady=10)
        body.pack(side="left", fill="both", expand=True)

        hdr = tk.Frame(body, bg=C.GLASS_3)
        hdr.pack(fill="x", pady=(0, 6))

        tk.Label(hdr, text="🖥️ Screen access required", font=(F._PRIMARY, F.MD, "bold"),
                 bg=C.GLASS_3, fg=C.FG_1).pack(side="left")

        model_name = payload_dict.get("model", "Cloud Model")
        tk.Label(hdr, text=f"  {model_name} (Cloud)  ", font=(F._FALLBACK, F.XS, "bold"),
                 bg="#1E293B", fg="#38BDF8", padx=4, pady=1).pack(side="left", padx=8)

        tk.Label(hdr, text=ts, font=(F._FALLBACK, F.XS),
                 bg=C.GLASS_3, fg=C.FG_3).pack(side="right")

        desc_text = (
            f"The selected cloud model ({model_name}) needs access to your current screen to continue this task.\n\n"
            f"Information that may be shared:\n"
            f"  • Current application/window\n"
            f"  • Relevant UI information\n"
            f"  • Required screen region\n\n"
            f"No screen information will be shared until you approve."
        )

        tk.Label(body, text=desc_text, font=(F._FALLBACK, F.SM), bg=C.GLASS_3, fg=C.FG_2,
                 justify="left", anchor="w").pack(fill="x", pady=(2, 8))

        ctrl = tk.Frame(body, bg=C.GLASS_3)
        ctrl.pack(fill="x", pady=(4, 0))

        def _do_once():
            btn_once.config(state="disabled")
            btn_session.config(state="disabled")
            btn_deny.config(state="disabled")
            card.config(highlightbackground=C.OK_L if hasattr(C, 'OK_L') else "#10B981")
            on_decision("allow once")

        def _do_session():
            btn_once.config(state="disabled")
            btn_session.config(state="disabled")
            btn_deny.config(state="disabled")
            card.config(highlightbackground=C.OK_L if hasattr(C, 'OK_L') else "#10B981")
            on_decision("allow for session")

        def _do_deny():
            btn_once.config(state="disabled")
            btn_session.config(state="disabled")
            btn_deny.config(state="disabled")
            card.config(highlightbackground=C.ERR_L if hasattr(C, 'ERR_L') else "#EF4444")
            on_decision("deny")

        btn_once = tk.Button(ctrl, text="[ Allow Once ]", font=(F._PRIMARY, F.SM, "bold"),
                             bg=C.BLUE, fg="white", activebackground=C.BLUE_L, activeforeground="white",
                             relief="flat", bd=0, padx=12, pady=5, cursor="hand2", command=_do_once)
        btn_once.pack(side="left", padx=(0, 6))

        btn_session = tk.Button(ctrl, text="[ Allow for Session ]", font=(F._PRIMARY, F.SM, "bold"),
                                bg="#0D9488", fg="white", activebackground="#14B8A6", activeforeground="white",
                                relief="flat", bd=0, padx=12, pady=5, cursor="hand2", command=_do_session)
        btn_session.pack(side="left", padx=(0, 6))

        btn_deny = tk.Button(ctrl, text="[ Deny ]", font=(F._FALLBACK, F.SM),
                             bg=C.BG_C2, fg=C.FG_1, activebackground=C.BG_S, activeforeground=C.FG_1,
                             relief="flat", bd=0, padx=12, pady=5, cursor="hand2", command=_do_deny)
        btn_deny.pack(side="left")

        self._bind_scroll(outer)
        self._scroll_to_bottom(force=True)
        return outer

