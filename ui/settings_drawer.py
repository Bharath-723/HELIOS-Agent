"""
ui/settings_drawer.py — HELIOS Settings Drawer
================================================
Right-side overlay drawer that slides in over the content panel.

Tabs
  General       — processing mode (auto/local/cloud), language, auto-scroll
  Appearance    — theme selection (dark/light/system), reduced motion, high contrast, font size
  Voice         — language, timeout
  Privacy       — save diagnostics, save log
  Performance   — telemetry refresh, thread priority
  Developer     — Enable Developer Mode (reveals Memory & CAHRA pages in rail)
"""

from __future__ import annotations
import tkinter as tk
from .theme import C, F, S, ThemeManager
from .icon_manager import I
from .sound_manager import SoundManager


class SettingsDrawer:
    """Settings overlay drawer containing General, Appearance, Voice, Privacy, Performance, and Developer panels."""

    TABS = ["General", "Appearance", "Voice", "Privacy", "Performance", "Developer", "Recently Deleted"]
    WIDTH = 380

    def __init__(self, parent: tk.Widget,
                 get_settings: callable,
                 save_settings: callable,
                 on_dev_mode_change: callable = None,
                 agent=None) -> None:
        self._parent             = parent
        self._get_settings       = get_settings
        self._save_settings       = save_settings
        self._on_dev_mode_change = on_dev_mode_change
        self.agent               = agent
        self._active_tab         = "General"
        self._visible            = False

        self._vars: dict[str, tk.Variable] = {}

        self._build()
        ThemeManager.add_listener(self._on_theme_changed)

    # ─────────────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # Dim overlay frame
        self._overlay = tk.Frame(self._parent, bg=C.BG_OVERLAY)
        self._overlay.bind("<ButtonRelease-1>", lambda e: self.close_())

        # Main drawer frame — GLASS_4 level surface (elevated over content panel)
        self._drawer = tk.Frame(self._parent, bg=C.GLASS_4,
                                width=self.WIDTH,
                                highlightthickness=1,
                                highlightbackground=C.GLASS_BD_4)
        self._drawer.pack_propagate(False)

        # Header row — title + close
        self._hdr = tk.Frame(self._drawer, bg=C.GLASS_4, height=56)
        self._hdr.pack(fill="x")
        self._hdr.pack_propagate(False)

        self._lbl_title = tk.Label(self._hdr, text=f"  {I.SETTINGS}  Settings",
                                   font=(F._PRIMARY, F.LG, "bold"),
                                   bg=C.GLASS_4, fg=C.FG_1)
        self._lbl_title.pack(side="left", pady=14)

        self._lbl_close = tk.Label(self._hdr, text=I.CLOSE,
                                   font=(F._FALLBACK, F.MD),
                                   bg=C.GLASS_4, fg=C.FG_3,
                                   cursor="hand2", padx=14)
        self._lbl_close.pack(side="right")
        self._lbl_close.bind("<ButtonRelease-1>", lambda e: self.close_())

        def _close_hover(e): self._lbl_close.configure(fg=C.ERR_L)
        def _close_leave(e): self._lbl_close.configure(fg=C.FG_3)
        self._lbl_close.bind("<Enter>", _close_hover)
        self._lbl_close.bind("<Leave>", _close_leave)

        self.sep1 = tk.Frame(self._drawer, bg=C.GLASS_BD_4, height=1)
        self.sep1.pack(fill="x")

        # Tab bar — compact scrollable pill tabs
        self._tab_bar = tk.Frame(self._drawer, bg=C.GLASS_4, pady=6)
        self._tab_bar.pack(fill="x")
        self._tab_btns: dict[str, tk.Label] = {}

        r1 = tk.Frame(self._tab_bar, bg=C.GLASS_4)
        r1.pack(fill="x", pady=1)
        r2 = tk.Frame(self._tab_bar, bg=C.GLASS_4)
        r2.pack(fill="x", pady=1)
        r3 = tk.Frame(self._tab_bar, bg=C.GLASS_4)
        r3.pack(fill="x", pady=1)

        for idx, tab in enumerate(self.TABS):
            if idx < 3:
                parent_r = r1
            elif idx < 5:
                parent_r = r2
            else:
                parent_r = r3
            btn = tk.Label(parent_r, text=tab,
                           font=(F._FALLBACK, F.XS, "bold"),
                           bg=C.GLASS_4, fg=C.FG_3,
                           cursor="hand2", padx=8, pady=5)
            btn.pack(side="left", fill="x", expand=True)
            btn.bind("<ButtonRelease-1>", lambda e, t=tab: self._switch_tab(t))
            self._tab_btns[tab] = btn

        self.sep2 = tk.Frame(self._drawer, bg=C.GLASS_BD_4, height=1)
        self.sep2.pack(fill="x")

        # Content frame (Scrollable)
        from .theme import ScrollableContainer
        self._scroll = ScrollableContainer(self._drawer, bg=C.GLASS_4)
        self._tab_frame = self._scroll.inner

        self._switch_tab("General")

    # ─────────────────────────────────────────────────────────────────────────
    def set_agent(self, agent) -> None:
        self.agent = agent

    def _switch_tab(self, tab: str) -> None:
        for t, btn in self._tab_btns.items():
            if t == tab:
                btn.configure(fg=C.BLUE, bg=C.GLASS_3)
            else:
                btn.configure(fg=C.FG_3, bg=C.GLASS_4)
        self._active_tab = tab

        # Clear content
        for w in self._tab_frame.winfo_children():
            w.destroy()

        s = self._get_settings() if self._get_settings else {}

        if tab == "General":
            self._tab_general(s)
        elif tab == "Appearance":
            self._tab_appearance(s)
        elif tab == "Voice":
            self._tab_voice(s)
        elif tab == "Privacy":
            self._tab_privacy(s)
        elif tab == "Performance":
            self._tab_performance(s)
        elif tab == "Developer":
            self._tab_developer(s)
        elif tab == "Recently Deleted":
            self._tab_recently_deleted(s)

        # Bind scroll triggers recursively
        self._scroll.bind_scroll(self._tab_frame)

    # ═════════════════════════════════════════════════════════════════════════
    # TABS CONTENT WIRING
    # ═════════════════════════════════════════════════════════════════════════
    def _tab_general(self, s: dict) -> None:
        parent = self._tab_frame

        self._section_lbl(parent, "Processing Mode")
        mode_var = tk.StringVar(value=s.get("mode", "auto"))
        self._vars["mode"] = mode_var
        for val, label in [("auto", "Auto (CAHRA Selects)"),
                            ("local", "Local Only"),
                            ("cloud", "Cloud Only")]:
            self._radio(parent, label, mode_var, val)

        self._sep(parent)
        self._section_lbl(parent, "System Language")
        lang_var = tk.StringVar(value=s.get("language", "en-IN"))
        self._vars["language"] = lang_var
        for val, label in [("en-IN", "English (India)"),
                            ("en-US", "English (US)"),
                            ("en-GB", "English (UK)")]:
            self._radio(parent, label, lang_var, val)

        self._sep(parent)
        self._section_lbl(parent, "Behavior")
        auto_scroll_var = tk.BooleanVar(value=s.get("auto_scroll", True))
        self._vars["auto_scroll"] = auto_scroll_var
        self._check(parent, "Auto-scroll chat messages", auto_scroll_var)

    def _tab_appearance(self, s: dict) -> None:
        parent = self._tab_frame

        self._section_lbl(parent, "Active Theme")
        theme_var = tk.StringVar(value=s.get("theme_mode", "dark"))
        self._vars["theme_mode"] = theme_var
        for val, label in [("dark", "Dark Mode"),
                            ("light", "Light Mode"),
                            ("system", "System Default")]:
            self._radio(parent, label, theme_var, val, command=self._apply_theme)

        self._sep(parent)
        self._section_lbl(parent, "Accessibility")
        rm_var = tk.BooleanVar(value=s.get("reduced_motion", False))
        self._vars["reduced_motion"] = rm_var
        self._check(parent, "Reduced Motion", rm_var)

        hc_var = tk.BooleanVar(value=s.get("high_contrast", False))
        self._vars["high_contrast"] = hc_var
        self._check(parent, "High Contrast", hc_var)

        self._sep(parent)
        self._section_lbl(parent, "Font Scale")
        font_var = tk.StringVar(value=s.get("font_scale", "Normal"))
        self._vars["font_scale"] = font_var
        for val in ["Small", "Normal", "Large"]:
            self._radio(parent, val, font_var, val)

    def _tab_voice(self, s: dict) -> None:
        parent = self._tab_frame

        self._section_lbl(parent, "Speech Recognition")
        vlang_var = tk.StringVar(value=s.get("voice_lang", "en-IN"))
        self._vars["voice_lang"] = vlang_var
        for val, label in [("en-IN", "English (India)"),
                            ("en-US", "English (US)"),
                            ("en-GB", "English (UK)")]:
            self._radio(parent, label, vlang_var, val)

        self._sep(parent)
        self._section_lbl(parent, "Audio Options")
        sound_var = tk.BooleanVar(value=s.get("sound", True))
        self._vars["sound"] = sound_var
        self._check(parent, "Enable Startup Sound", sound_var)

    def _tab_privacy(self, s: dict) -> None:
        parent = self._tab_frame

        self._section_lbl(parent, "Telemetry Logging")
        diag_var = tk.BooleanVar(value=s.get("save_diagnostics", True))
        self._vars["save_diagnostics"] = diag_var
        self._check(parent, "Log routing diagnostics", diag_var)

        log_var = tk.BooleanVar(value=s.get("save_log", True))
        self._vars["save_log"] = log_var
        self._check(parent, "Log session logs", log_var)

        self._sep(parent)
        self._section_lbl(parent, "Cloud Warnings")
        warn_var = tk.BooleanVar(value=s.get("routing_warnings", True))
        self._vars["routing_warnings"] = warn_var
        self._check(parent, "Warn when routed to Cloud", warn_var)

    def _tab_performance(self, s: dict) -> None:
        parent = self._tab_frame

        self._section_lbl(parent, "Telemetry Updates")
        refresh_var = tk.StringVar(value=s.get("telemetry_refresh", "2s"))
        self._vars["telemetry_refresh"] = refresh_var
        for val, label in [("1s", "High (1s refresh)"),
                            ("2s", "Standard (2s refresh)"),
                            ("5s", "Efficient (5s refresh)")]:
            self._radio(parent, label, refresh_var, val)

        self._sep(parent)
        self._section_lbl(parent, "Rendering Mode")
        fps_var = tk.StringVar(value=s.get("fps_limit", "30fps"))
        self._vars["fps_limit"] = fps_var
        for val, label in [("30fps", "Cinema (30 FPS)"),
                            ("15fps", "Battery Saver (15 FPS)")]:
            self._radio(parent, label, fps_var, val)

    def _tab_developer(self, s: dict) -> None:
        parent = self._tab_frame

        self._section_lbl(parent, "Developer Mode")
        dev_var = tk.BooleanVar(value=s.get("developer_mode", False))
        self._vars["developer_mode"] = dev_var
        self._check(parent, "Enable Developer Mode", dev_var, command=self._apply_dev_mode)

        self._sep(parent)
        tk.Label(parent, text="Developer Mode exposes the CAHRA Routing Panel and Memory Hierarchy Panel in the permanent Navigation Rail.",
                 font=(F._FALLBACK, F.XS), bg=C.GLASS_4, fg=C.FG_3, wraplength=260, justify="left").pack(anchor="w", padx=14)

    # ─────────────────────────────────────────────────────────────────────────
    def _radio(self, parent: tk.Widget, label: str, var: tk.Variable, val: str, command: callable = None) -> None:
        def _cmd():
            self._save()
            if command: command()

        rb = tk.Radiobutton(
            parent, text=label, variable=var, value=val,
            font=(F._FALLBACK, F.SM), bg=C.GLASS_4, fg=C.FG_2,
            activebackground=C.GLASS_4, activeforeground=C.FG_1,
            selectcolor=C.GLASS_3, command=_cmd
        )
        rb.pack(anchor="w", padx=16, pady=1)

    def _check(self, parent: tk.Widget, label: str, var: tk.Variable, command: callable = None) -> None:
        def _cmd():
            self._save()
            if command: command()

        cb = tk.Checkbutton(
            parent, text=label, variable=var,
            font=(F._FALLBACK, F.SM), bg=C.GLASS_4, fg=C.FG_2,
            activebackground=C.GLASS_4, activeforeground=C.FG_1,
            selectcolor=C.GLASS_3, command=_cmd
        )
        cb.pack(anchor="w", padx=16, pady=1)

    def _tab_recently_deleted(self, s: dict) -> None:
        parent = self._tab_frame
        self._section_lbl(parent, "Recently Deleted Chats (7-Day Retention)")

        from tkinter import messagebox

        if not self.agent or not hasattr(self.agent.history, "get_recently_deleted"):
            tk.Label(parent, text="No deleted sessions found.", font=(F._FALLBACK, F.SM), bg=C.GLASS_4, fg=C.FG_3, pady=16).pack()
            return

        deleted_list = self.agent.history.get_recently_deleted()
        if not deleted_list:
            tk.Label(parent, text="Trash is empty. No recently deleted chats.", font=(F._FALLBACK, F.SM), bg=C.GLASS_4, fg=C.FG_3, pady=16).pack()
            return

        for item in deleted_list:
            sid = item.get("id", "")
            title = item.get("title", sid)[:30]
            del_at = item.get("deleted_at", "")[:16].replace("T", " ")

            card = tk.Frame(parent, bg=C.GLASS_3, highlightthickness=1, highlightbackground=C.GLASS_BD_3, padx=8, pady=6)
            card.pack(fill="x", padx=10, pady=4)

            tk.Label(card, text=title, font=(F._FALLBACK, F.SM, "bold"), bg=C.GLASS_3, fg=C.FG_1).pack(anchor="w")
            tk.Label(card, text=f"Deleted: {del_at}", font=(F._FALLBACK, F.XS), bg=C.GLASS_3, fg=C.FG_3).pack(anchor="w")

            btn_row = tk.Frame(card, bg=C.GLASS_3)
            btn_row.pack(fill="x", pady=(4, 0))

            # Restore button
            btn_res = tk.Label(btn_row, text="↩ Restore", font=(F._FALLBACK, F.XS, "bold"), bg=C.BLUE_DIM, fg=C.FG_1, cursor="hand2", padx=6, pady=2)
            btn_res.pack(side="left")

            def on_restore(e, s_id=sid):
                self.agent.history.restore_session(s_id)
                self._switch_tab("Recently Deleted")

            btn_res.bind("<ButtonRelease-1>", on_restore)

            # Permanent delete button
            btn_perm = tk.Label(btn_row, text="🗑 Delete Permanently", font=(F._FALLBACK, F.XS, "bold"), bg=C.ERR_D, fg=C.ERR_L, cursor="hand2", padx=6, pady=2)
            btn_perm.pack(side="right")

            def on_perm_del(e, s_id=sid, t=title):
                if messagebox.askyesno("Confirm Permanent Deletion", f"Are you sure you want to permanently delete '{t}'?\nThis action cannot be undone."):
                    self.agent.history.permanent_delete(s_id)
                    self._switch_tab("Recently Deleted")

            btn_perm.bind("<ButtonRelease-1>", on_perm_del)

        self._sep(parent)

        # Delete All Permanently button at bottom
        btn_all = tk.Label(parent, text="🗑 Delete All Permanently", font=(F._FALLBACK, F.SM, "bold"), bg=C.ERR_D, fg=C.ERR_L, cursor="hand2", pady=8)
        btn_all.pack(fill="x", padx=14, pady=10)

        def on_del_all(e):
            if messagebox.askyesno("Confirm Delete All", "Are you sure you want to permanently delete ALL soft-deleted chats?\nThis action cannot be undone."):
                self.agent.history.permanent_delete_all()
                self._switch_tab("Recently Deleted")

        btn_all.bind("<ButtonRelease-1>", on_del_all)

    def _section_lbl(self, parent: tk.Widget, text: str) -> None:
        row = tk.Frame(parent, bg=C.GLASS_4)
        row.pack(fill="x", padx=14, pady=(12, 4))
        tk.Label(row, text=text,
                 font=(F._PRIMARY, F.XS, "bold"),
                 bg=C.GLASS_4, fg=C.FG_2, pady=2).pack(anchor="w")
        tk.Frame(row, bg=C.GLASS_BD_3, height=1).pack(fill="x", pady=(2, 0))

    def _sep(self, parent: tk.Widget) -> None:
        tk.Frame(parent, bg=C.GLASS_BD_3, height=1).pack(fill="x", padx=10, pady=6)

    # ─────────────────────────────────────────────────────────────────────────
    def _save(self) -> None:
        if not self._save_settings:
            return
        data = {k: v.get() for k, v in self._vars.items()}
        self._save_settings(data)

    def _apply_theme(self) -> None:
        mode = self._vars["theme_mode"].get()
        ThemeManager.set_mode(mode)

    def _apply_dev_mode(self) -> None:
        val = self._vars["developer_mode"].get()
        if self._on_dev_mode_change:
            self._on_dev_mode_change(val)

    # ═════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═════════════════════════════════════════════════════════════════════════
    def open_(self) -> None:
        if self._visible:
            return
        self._visible = True

        self._overlay.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._drawer.place(relx=1.0, rely=0.0, x=-self.WIDTH, width=self.WIDTH, relheight=1.0)
        self._drawer.lift()
        SoundManager.nav_switch()

    def close_(self) -> None:
        if not self._visible:
            return
        self._visible = False
        self._overlay.place_forget()
        self._drawer.place_forget()
        SoundManager.nav_switch()

    def toggle(self) -> None:
        if self._visible: self.close_()
        else: self.open_()

    # ─────────────────────────────────────────────────────────────────────────
    def _on_theme_changed(self) -> None:
        self._overlay.configure(bg=C.BG_OVERLAY)
        self._drawer.configure(bg=C.GLASS_4, highlightbackground=C.GLASS_BD_4)
        self._hdr.configure(bg=C.GLASS_4)
        self._lbl_title.configure(bg=C.GLASS_4, fg=C.FG_1)
        self._lbl_close.configure(bg=C.GLASS_4, fg=C.FG_3)
        self.sep1.configure(bg=C.GLASS_BD_4)
        self._tab_bar.configure(bg=C.GLASS_4)
        self.sep2.configure(bg=C.GLASS_BD_4)
        self._tab_frame.configure(bg=C.GLASS_4)

        for t, btn in self._tab_btns.items():
            if t == self._active_tab:
                btn.configure(fg=C.BLUE, bg=C.GLASS_3)
            else:
                btn.configure(fg=C.FG_3, bg=C.GLASS_4)

        self._switch_tab(self._active_tab)
