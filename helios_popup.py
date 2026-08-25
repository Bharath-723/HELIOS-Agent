"""
HELIOS v3.3 — Cognitive Operating System
==========================================
Application orchestrator.

Handles:
  • Winreg system theme synchronization + 300ms animated fade transition
  • Window size and position memory (data/window_settings.json)
  • Bottom-right manual resize grip controller
  • Greeting and home screen suggested actions
  • 1.5s thinking indicator delay threshold
  • Ctrl+K Command Palette + Ctrl+Shift+P Global Search
  • Model label click-to-toggle floating selector drawer
  • Cloud routing sensitive warning scanner
  • Telemetry loop updates (diagnostics circular dials)
"""

# ── Venv self-bootstrap ───────────────────────────────────────────────────────
import sys as _sys, os as _os, subprocess as _sub
_here    = _os.path.dirname(_os.path.abspath(__file__))
_venv_py = _os.path.join(_here, "venv", "Scripts", "python.exe")
_in_venv = (
    _os.path.normcase(getattr(_sys, "prefix", "")) ==
    _os.path.normcase(_os.path.join(_here, "venv"))
)
if _os.path.exists(_venv_py) and not _in_venv:
    _sub.Popen([_venv_py] + _sys.argv)
    _sys.exit(0)
del _here, _venv_py, _in_venv, _sub
# ──────────────────────────────────────────────────────────────────────────────

import sys
import os
import json
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk

# ── UI modules ────────────────────────────────────────────────────────────────
from ui.theme import C, F, S, W as WT, A, ThemeManager
from ui.sound_manager import SoundManager
from ui.animation_engine import AnimationEngine
from ui.ambient_background import AmbientBackground
from ui.header import Header
from ui.navigation_rail import NavigationRail
from ui.status_bar import StatusBar
from ui.chat_view import ChatView
from ui.input_panel import InputPanel
from ui.history_panel import HistoryPanel
from ui.models_panel import ModelsPanel
from ui.routing_panel import RoutingPanel
from ui.memory_panel import MemoryPanel
from ui.diagnostics_panel import DiagnosticsPanel
from ui.desktop_panel import DesktopPanel
from ui.settings_drawer import SettingsDrawer
from core.system import paths_manager, environment_manager, runtime_manager, shutdown_manager

_SETTINGS_FILE = paths_manager.get_ui_settings_path()
_WINDOW_FILE   = paths_manager.get_window_settings_path()
_SIMPLE_PROMPTS = {"hi", "hello", "thanks", "yes", "no", "good morning", "good evening", "good afternoon", "thank you"}


class HELIOSApp:
    """HELIOS Cognitive Operating System Orchestrator."""
    _instance = None

    def __init__(self) -> None:
        if HELIOSApp._instance is not None:
            import logging
            logging.getLogger("helios.ui").warning("[HELIOS WINDOW] Existing HELIOSApp instance detected! Reusing existing window.")
            return

        HELIOSApp._instance = self
        self.runtime_ctx = runtime_manager.initialize_runtime()
        self.root = tk.Tk()
        self.root.report_callback_exception = self._on_tkinter_error
        
        # ── Core state ────────────────────────────────────────────────────────
        self.agent = None
        self.q: queue.Queue = queue.Queue()
        self._current_panel = "chat"
        self._ui_mode = "DESKTOP_VIEW"
        self._prev_geom = {"w": WT.WIDTH, "h": WT.HEIGHT, "x": -1, "y": -1}
        self._drag_sx = self._drag_sy = 0
        self._resize_w = self._resize_h = 0
        self._resize_x = self._resize_y = 0
        
        self._settings = self._load_settings()
        self._start_ts = time.time()
        
        self._auto_route = True
        ThemeManager.set_mode(self._settings.get("theme_mode", "dark"))
        SoundManager.mute(not self._settings.get("sound", True))

        self._setup_window()

        # ── Two-Layer Composition Architecture ───────────────────────────────
        # MAIN contains two sibling layers occupying the same area:
        #   BACKGROUND_LAYER  — AmbientBackground canvas (always below)
        #   FOREGROUND_LAYER  — All UI widgets (header, nav, chat, input)
        # foreground_layer.lift() is called after both layers exist,
        # guaranteeing foreground is always visually above background.
        # AmbientBackground NEVER calls lift()/lower() on itself.
        # NavigationRail tooltips NEVER call root.lift().
        self._build_main_container()  # creates self.main
        self._build_layers()          # creates background_layer + foreground_layer, calls foreground_layer.lift()

        # Background lives entirely inside background_layer
        self.bg = AmbientBackground(self.background_layer, WT.WIDTH, WT.HEIGHT)

        # ── Animation engine ──────────────────────────────────────────────────
        self.anim = AnimationEngine(self.background_layer, self.bg.canvas, WT.WIDTH, WT.HEIGHT)

        # ── UI Layout inside foreground_layer ────────────────────────────────
        # Pack order: boundaries first (header, status, input), then expanding body.
        # This ensures the body (chat) gets all remaining vertical space.
        self._build_header()        # → pack(side="top", fill="x")
        self._build_status_bar()    # → pack(side="bottom", fill="x")
        self._build_input()         # → pack(side="bottom", fill="x")
        self._build_content_area()  # → pack(side="top", fill="both", expand=True)
        self._build_panels()
        self._build_settings_drawer()

        # Enforce foreground above background after all widgets created
        self.foreground_layer.lift()

        # Register avatar pulse
        av_canvas, av_item = self.header.get_avatar_info()
        self.anim.register_avatar(av_canvas, av_item)
        self.anim.start()

        # Apply settings
        self.nav.set_developer_mode(self._settings.get("developer_mode", False))

        # ── Resizing & Model selector click hooks ─────────────────────────────
        self._wire_interactive_hooks()

        # ── Key bindings ──────────────────────────────────────────────────────
        self.root.bind("<Control-k>", lambda e: self._open_cmd_palette())
        self.root.bind("<Control-Shift-P>", lambda e: self._open_global_search())
        self.root.bind("<Escape>", lambda e: self._on_escape())
        
        # Custom virtual events
        self.root.bind("<<LoadSession>>", lambda e: self._on_load_session(self._get_clipboard_text()))
        self.root.bind("<<EditUserText>>", lambda e: self._edit_command_entry(e))
        self.root.bind("<<SaveNote>>", lambda e: self._save_agent_note(e))
        self.root.bind("<<Regenerate>>", lambda e: self._regenerate_last())

        # ── 8-Directional Resize Binds ────────────────────────────────────────
        self._resize_dir = ""
        self._resize_active = False
        self.root.bind_all("<Motion>", self._on_root_motion)
        self.root.bind_all("<Button-1>", self._on_root_click, "+")
        self.root.bind_all("<B1-Motion>", self._on_root_drag, "+")
        self.root.bind_all("<ButtonRelease-1>", self._on_root_release, "+")

        # ── Load Agent & Telemetry ───────────────────────────────────────────
        self._load_agent()
        self.diag_p.start()

        # ── Fade in startup & UI Watchdog ─────────────────────────────────────
        self.root.after(100, self._startup_sequence)
        self.root.after(2000, self._start_ui_watchdog)
        self._poll()

        self.root.mainloop()

    def _on_tkinter_error(self, exc, val, tb) -> None:
        import traceback, logging
        log_ui = logging.getLogger("helios.ui")
        err_msg = "".join(traceback.format_exception(exc, val, tb))
        log_ui.error("[UI ERROR] Callback exception: %s\n%s", val, err_msg)
        try:
            if hasattr(self, "chat") and self.chat:
                self.chat.add_system_notice(f"⚠ UI Warning: {val}")
        except Exception:
            pass

    def _start_ui_watchdog(self) -> None:
        """UI Watchdog: checks real geometry + mapping state. Logs [UI-INVARIANT] every cycle."""
        import logging
        log_ui = logging.getLogger("helios.ui")
        try:
            root_alive = hasattr(self, "root") and self.root.winfo_exists()
            if not root_alive:
                return

            chat_alive  = hasattr(self, "chat") and hasattr(self.chat, "frame") and self.chat.frame.winfo_exists()
            msgs_alive  = hasattr(self, "chat") and hasattr(self.chat, "msgs")  and self.chat.msgs.winfo_exists()
            panel_alive = hasattr(self, "panel_area") and self.panel_area.winfo_exists()
            fg_alive    = hasattr(self, "foreground_layer") and self.foreground_layer.winfo_exists()
            bg_alive    = hasattr(self, "background_layer") and self.background_layer.winfo_exists()

            # Real geometry check — existence ≠ visibility
            chat_mapped  = self.chat.frame.winfo_ismapped()   if chat_alive  else False
            chat_w       = self.chat.frame.winfo_width()      if chat_alive  else 0
            chat_h       = self.chat.frame.winfo_height()     if chat_alive  else 0
            chat_x       = self.chat.frame.winfo_x()          if chat_alive  else 0
            chat_y       = self.chat.frame.winfo_y()          if chat_alive  else 0
            fg_mapped    = self.foreground_layer.winfo_ismapped() if fg_alive else False
            bg_mapped    = self.background_layer.winfo_ismapped() if bg_alive else False

            # foreground_layer must always be above background_layer
            # Enforce it here as the safety net (architecture ensures it, this is belt+suspenders)
            fg_above_bg = True
            if fg_alive and bg_alive:
                try:
                    # Re-lift foreground if background somehow rose above it
                    self.foreground_layer.lift()
                except Exception:
                    fg_above_bg = False

            log_ui.debug(
                "[UI-INVARIANT]\n"
                "chat_exists=%s\nchat_mapped=%s\nchat_x=%s\nchat_y=%s\n"
                "chat_width=%s\nchat_height=%s\nforeground_mapped=%s\n"
                "background_mapped=%s\nforeground_above_background=%s",
                chat_alive, chat_mapped, chat_x, chat_y,
                chat_w, chat_h, fg_mapped, bg_mapped, fg_above_bg
            )

            # Log invariant failure
            if chat_alive and chat_mapped and (chat_w == 0 or chat_h == 0):
                log_ui.warning(
                    "[UI-INVARIANT-FAIL] Chat viewport has zero dimensions: w=%s h=%s",
                    chat_w, chat_h
                )

            # Rebuild ChatView only if widget is actually destroyed (not just zero-sized)
            if panel_alive and (not chat_alive or not msgs_alive):
                log_ui.warning("[UI RENDER REPAIR] ChatView widget destroyed — rebuilding.")
                self.chat = ChatView(
                    self.panel_area, anim_engine=getattr(self, "anim", None),
                    on_home_action=self._insert_home_action,
                    on_trigger_file=self._trigger_file_selection,
                    on_drag_start=self._drag_start,
                    on_drag_do=self._drag_do
                )
                self.panels["chat"] = self.chat.frame
                self._show_panel("chat")
                if self.agent:
                    self._on_new_session()
            elif msgs_alive:
                if len(self.chat.msgs.winfo_children()) == 0 and getattr(self.chat, "_home_view", None) is None:
                    log_ui.info("[UI RENDER REPAIR] Feed empty — restoring Home Screen.")
                    self.chat.show_home_screen()

        except Exception as ex:
            logging.getLogger("helios.ui").error("[UI WATCHDOG ERROR] %s", ex)
        finally:
            if hasattr(self, "root") and self.root.winfo_exists():
                self.root.after(2000, self._start_ui_watchdog)

    # ═════════════════════════════════════════════════════════════════════════
    # INTERACTIVE HOOKS & RESIZING
    # ═════════════════════════════════════════════════════════════════════════
    def _wire_interactive_hooks(self) -> None:
        # Resize grip binds
        self.status_bar.resize_grip.bind("<Button-1>", self._resize_start)
        self.status_bar.resize_grip.bind("<B1-Motion>", self._resize_do)

        # Model label click -> toggles input panel floating selector drawer
        self.status_bar._lbl_model.bind("<ButtonRelease-1>", lambda e: self.inp._toggle_model_drawer())
        self.header.status_lbl.bind("<ButtonRelease-1>", lambda e: self.inp._toggle_model_drawer())
        self.header.avatar_cv.bind("<ButtonRelease-1>", lambda e: self.inp._toggle_model_drawer())

    def _resize_start(self, e: tk.Event) -> None:
        self._resize_w = self.root.winfo_width()
        self._resize_h = self.root.winfo_height()
        self._resize_x = e.x_root
        self._resize_y = e.y_root

    def _resize_do(self, e: tk.Event) -> None:
        dw = e.x_root - self._resize_x
        dh = e.y_root - self._resize_y
        nw = max(WT.MIN_W, self._resize_w + dw)
        nh = max(WT.MIN_H, self._resize_h + dh)
        self.root.geometry(f"{nw}x{nh}")

    # ═════════════════════════════════════════════════════════════════════════
    # WINDOW SETUP
    # ═════════════════════════════════════════════════════════════════════════
    def _get_hwnd(self) -> int:
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                return hwnd if hwnd else self.root.winfo_id()
            except Exception:
                pass
        return 0

    def _setup_window_native_styles(self) -> None:
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = self._get_hwnd()
                if hwnd:
                    GWL_EXSTYLE = -20
                    WS_EX_APPWINDOW = 0x00040000
                    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_APPWINDOW)
                    from core.desktop_session import ScreenObserver
                    ScreenObserver.register_helios_hwnd(hwnd)
            except Exception:
                pass

    def _setup_window(self) -> None:
        self.root.title("HELIOS")
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", 1.0)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=C.BG)

        self._setup_window_native_styles()

        # Load size and position
        w, h, x, y = WT.WIDTH, WT.HEIGHT, -1, -1
        try:
            if _WINDOW_FILE.exists():
                geom = json.loads(_WINDOW_FILE.read_text())
                w = geom.get("width", WT.WIDTH)
                h = geom.get("height", WT.HEIGHT)
                x = geom.get("x", -1)
                y = geom.get("y", -1)
        except Exception:
            pass

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        if x < 0 or x + w > sw or y < 0 or y + h > sh:
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)

        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(WT.MIN_W, WT.MIN_H)

        self.root.bind("<Configure>", self._on_configure)

    def _on_configure(self, e) -> None:
        if e.widget == self.root:
            if getattr(self, "_resize_after_id", None):
                try:
                    self.root.after_cancel(self._resize_after_id)
                except Exception:
                    pass
            self._resize_after_id = self.root.after(16, lambda w=e.width, h=e.height: self._apply_coalesced_resize(w, h))

    def _apply_coalesced_resize(self, width: int, height: int) -> None:
        self._resize_after_id = None
        if hasattr(self, "anim"):
            self.anim.resize(width, height)
        if hasattr(self, "bg"):
            self.bg.resize(width, height)
        self._save_window_geometry()

    def _save_window_geometry(self) -> None:
        try:
            _WINDOW_FILE.parent.mkdir(parents=True, exist_ok=True)
            geom = {
                "width":  self.root.winfo_width(),
                "height": self.root.winfo_height(),
                "x":      self.root.winfo_x(),
                "y":      self.root.winfo_y()
            }
            _WINDOW_FILE.write_text(json.dumps(geom))
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════════════════════
    # BUILD LAYERS
    # ═════════════════════════════════════════════════════════════════════════
    def _build_main_container(self) -> None:
        b = WT.BORDER
        self.main = tk.Frame(self.root, bg=C.BG, bd=0)
        self.main.place(x=b, y=b, relwidth=1.0, relheight=1.0, width=-2*b, height=-2*b)

    def _build_layers(self) -> None:
        """
        Two-layer composition architecture.

        BACKGROUND_LAYER and FOREGROUND_LAYER are siblings inside self.main,
        both placed at (0, 0, relwidth=1, relheight=1).

        foreground_layer.lift() is called immediately after both exist.
        This is the ONLY place lift() is called — never inside AmbientBackground,
        never inside NavigationRail tooltips.

        All UI widgets (header, nav, chat, input, status) live inside foreground_layer.
        AmbientBackground canvas lives inside background_layer.

        Even if some code elsewhere calls lift() or lower() on any child widget,
        the two-layer boundary is maintained by the watchdog re-calling
        foreground_layer.lift() periodically.
        """
        # Background layer — receives AmbientBackground canvas
        self.background_layer = tk.Frame(self.main, bg=C.BG, bd=0)
        self.background_layer.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.bg = AmbientBackground(self.background_layer, WT.WIDTH, WT.HEIGHT)

        # Foreground layer — receives all UI components
        self.foreground_layer = tk.Frame(self.main, bg=C.BG, bd=0)
        self.foreground_layer.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        # CRITICAL: foreground must be above background
        self.foreground_layer.lift()

    def _build_header(self) -> None:
        self.header = Header(
            self.foreground_layer,
            on_close      = self._on_close,
            on_minimize   = self._on_minimize,
            on_maximize   = self._on_maximize,
            on_settings   = self._toggle_settings,
            on_drag_start = self._drag_start,
            on_drag_do    = self._drag_do,
            on_drag_end   = self._drag_end,
            on_auto_toggle = self._toggle_auto_route,
            on_compact_toggle = self._toggle_compact_mode,
        )
        self.header.frame.pack(side="top", fill="x")

    def _toggle_compact_mode(self) -> None:
        """Instant responsive viewport mode toggle (<50ms). Preserves agent state & session."""
        if self._ui_mode == "DESKTOP_VIEW":
            self._prev_geom = {
                "w": self.root.winfo_width(),
                "h": self.root.winfo_height(),
                "x": self.root.winfo_x(),
                "y": self.root.winfo_y()
            }
            self._ui_mode = "COMPACT_VIEW"
            if hasattr(self, "nav") and hasattr(self.nav, "frame"):
                self.nav.frame.pack_forget()
            new_x = max(0, self._prev_geom["x"])
            new_y = max(0, self._prev_geom["y"])
            self.root.geometry(f"420x760+{new_x}+{new_y}")
            self.header.set_compact_state(True)
        else:
            self._ui_mode = "DESKTOP_VIEW"
            if hasattr(self, "nav") and hasattr(self.nav, "frame"):
                self.nav.frame.pack(side="left", fill="y", before=self.panel_area)
            pw = self._prev_geom.get("w", WT.WIDTH)
            ph = self._prev_geom.get("h", WT.HEIGHT)
            px = self._prev_geom.get("x", 100)
            py = self._prev_geom.get("y", 100)
            self.root.geometry(f"{pw}x{ph}+{px}+{py}")
            self.header.set_compact_state(False)

    def _build_content_area(self) -> None:
        # Body row — fills all remaining vertical space after header/input/status
        self.content_row = tk.Frame(self.foreground_layer, bg=C.BG)
        self.content_row.pack(side="top", fill="both", expand=True)

        # NavigationRail receives foreground_layer reference for safe tooltip placement
        self.nav = NavigationRail(
            self.content_row, on_nav=self._on_nav,
            tooltip_parent=self.foreground_layer,
        )
        self.nav.frame.pack(side="left", fill="y")

        # Panel area — owns the full expandable region
        self.panel_area = tk.Frame(self.content_row, bg=C.BG_S)
        self.panel_area.pack(side="left", fill="both", expand=True)

    def _build_panels(self) -> None:
        self.panels: dict[str, tk.Frame] = {}

        self.chat = ChatView(
            self.panel_area, anim_engine=self.anim,
            on_home_action=self._insert_home_action,
            on_trigger_file=self._trigger_file_selection,
            on_drag_start=self._drag_start,
            on_drag_do=self._drag_do
        )
        self.panels["chat"] = self.chat.frame

        self.memory_p = MemoryPanel(self.panel_area)
        self.panels["memory"] = self.memory_p.frame

        self.routing_p = RoutingPanel(self.panel_area)
        self.panels["routing"] = self.routing_p.frame

        self.models_p = ModelsPanel(self.panel_area, on_select=self._on_model_select)
        self.panels["models"] = self.models_p.frame

        self.history_p = HistoryPanel(
            self.panel_area,
            on_load  = self._on_load_session,
            on_new   = self._on_new_session,
            on_clear = self._on_clear_history,
        )
        self.panels["history"] = self.history_p.frame

        self.diag_p = DiagnosticsPanel(self.panel_area)
        self.panels["diagnostics"] = self.diag_p.frame
        self.panels["activity"]    = self.diag_p.frame

        self.desktop_p = DesktopPanel(self.panel_area)
        self.panels["desktop"]     = self.desktop_p.frame

        self._show_panel("chat")

    def _show_panel(self, key: str) -> None:
        target_frame = self.panels.get(key)
        if not target_frame:
            return
        unique_frames = set(self.panels.values())
        for frame in unique_frames:
            if frame == target_frame:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        self._current_panel = key

    def _build_input(self) -> None:
        self.inp = InputPanel(
            self.foreground_layer,
            on_send         = self._on_send,
            on_voice_result = self._on_voice_result,
            on_status       = self._on_status_msg,
            on_model_change = self._on_model_select,
            on_auto_toggle  = self._toggle_auto_route,
            on_screen_context_toggle = self._on_screen_context_toggle
        )
        self.inp.frame.pack(side="bottom", fill="x")

    def _on_screen_context_toggle(self, enabled: bool) -> None:
        if hasattr(self, "agent") and self.agent:
            self.agent.set_screen_context_enabled(enabled)

    def _build_status_bar(self) -> None:
        self.status_bar = StatusBar(self.foreground_layer)
        self.status_bar.frame.pack(fill="x", side="bottom")

    def _build_settings_drawer(self) -> None:
        self.settings_drawer = SettingsDrawer(
            self.panel_area,
            get_settings  = lambda: self._settings,
            save_settings = self._save_settings,
            on_dev_mode_change = self._dev_mode_changed
        )

    # ─────────────────────────────────────────────────────────────────────────
    def _on_configure(self, e) -> None:
        if e.widget == self.root:
            if hasattr(self, "anim"):
                self.anim.resize(e.width, e.height)
            if hasattr(self, "bg"):
                self.bg.resize(e.width, e.height)
            # Re-enforce foreground above background on every resize
            if hasattr(self, "foreground_layer") and self.foreground_layer.winfo_exists():
                self.foreground_layer.lift()
            self._save_window_geometry()

    # ═════════════════════════════════════════════════════════════════════════
    # STARTUP
    # ═════════════════════════════════════════════════════════════════════════
    def _startup_sequence(self) -> None:
        steps = A.FADE_STEPS
        target_alpha = WT.ALPHA

        def _step(i=0):
            if i > steps:
                self.root.attributes("-alpha", target_alpha)
                self._post_startup()
                return
            alpha = (i / steps) * target_alpha
            self.root.attributes("-alpha", alpha)
            self.root.after(A.FADE_IN // steps, lambda: _step(i + 1))

        _step(0)
        SoundManager.startup()

    def _post_startup(self) -> None:
        self.header.set_status("Loading agent…")
        self.anim.set_state("thinking")

    # ═════════════════════════════════════════════════════════════════════════
    # AGENT LOADER
    # ═════════════════════════════════════════════════════════════════════════
    def _load_agent(self) -> None:
        def _run():
            try:
                from agent import HELIOSAgent
                a = HELIOSAgent()
                self.q.put(("agent_ready", a))
            except Exception as ex:
                import traceback
                self.q.put(("agent_error", str(ex) + "\n" + traceback.format_exc()))
        threading.Thread(target=_run, daemon=True).start()

    def _agent_ready(self, agent) -> None:
        self.agent = agent
        agent.set_ui_notify(lambda msg: self.q.put(("reminder", msg)))
        
        current_model = getattr(agent.llm, "active_cloud_model", None) or getattr(agent.llm, "ollama_model", "gemma3")
        mode_str = "AUTO" if getattr(self, "_auto_route", True) else "MANUAL"
        
        self.anim.set_state("idle")
        self._update_all_model_displays(current_model, mode_str)
        
        self.history_p.refresh(agent)
        self.settings_drawer.set_agent(agent)
        
        if self.chat._home_view:
            self.chat._home_view.refresh(agent)

    def _toggle_auto_route(self) -> None:
        """Toggle Auto-Routing ON/OFF."""
        self._auto_route = not getattr(self, "_auto_route", True)
        if self.agent and hasattr(self.agent, "llm"):
            if self._auto_route:
                self.agent.llm.set_mode("auto")
            else:
                active_m = getattr(self.agent.llm, "active_cloud_model", None)
                self.agent.llm.set_mode("online" if active_m else "offline")

        is_auto = self._auto_route
        self.header.set_auto_route_state(is_auto)

        curr_m = getattr(self.agent.llm, "active_cloud_model", None) or getattr(self.agent.llm, "ollama_model", "gemma3") if self.agent else "gemma3"
        mode_str = "AUTO" if is_auto else "MANUAL"
        self._update_all_model_displays(curr_m, mode_str)
        SoundManager.toggle()

    def _update_all_model_displays(self, model: str, mode: str = None) -> None:
        """Synchronize model display across all 5 UI components (Header, Status, Input, Gallery, Diag)."""
        if not mode:
            mode = "AUTO" if getattr(self, "_auto_route", True) else "MANUAL"
            
        self.header.set_model_status(model, mode, "Ready")
        self.status_bar.update(model=model, mode=mode, memory="L1+L2", state="Ready")
        self.inp.set_active_model(model)
        self.inp.update_context(model=model, mode=mode)
        if hasattr(self, "models_p"):
            self.models_p.set_active(model)
        if hasattr(self, "diag_p"):
            self.diag_p.update_model_name(model)

    def _dev_mode_changed(self, enabled: bool) -> None:
        self.nav.set_developer_mode(enabled)

    # ═════════════════════════════════════════════════════════════════════════
    # SEND & PROCESS
    # ═════════════════════════════════════════════════════════════════════════
    def _on_send(self, text: str, files: list[str] = None) -> None:
        if files is None:
            files = []
        if not self.agent:
            self.chat.add_system_notice("⚠ Agent loading. Please wait.")
            return

        if self._current_panel != "chat":
            self._show_panel("chat")
            self.nav.set_active("chat")

        display_text = text
        prompt_text  = text
        if files:
            tags = self._build_file_tags(files)
            prompt_text = (text + "\n" + tags).strip() if text else tags
            display_text = text or f"[{len(files)} file(s) attached]"

        # Check if user requested opening system camera app in search bar
        lower_t = text.lower().strip()
        if lower_t in ["open camera", "launch camera", "start camera", "turn on camera", "open system camera"]:
            self.chat.add_user_message(display_text)
            try:
                import subprocess
                subprocess.Popen("start microsoft.windows.camera:", shell=True)
                self.chat.add_helios_message("📷 Opened Windows System Camera application.")
            except Exception as exc:
                self.chat.add_system_notice(f"Failed to launch camera: {exc}")
            return

        # Check if user is triggering web search or desktop search -> switch to floating mode
        search_triggers = ["search", "web", "google", "find", "open", "launch", "lookup", "youtube", "weather"]
        if any(lower_t.startswith(kw) or f" {kw} " in f" {lower_t} " for kw in search_triggers):
            if getattr(self, "_is_maximized", False):
                self._set_floating_mode()

        # Outgoing Cloud privacy checks
        self._check_cloud_privacy(prompt_text)

        self.chat.add_user_message(display_text, attachments=files)
        self._start_ts = time.time()

        # Simple prompt instant-replies short-circuit
        is_simple = text.lower().strip() in _SIMPLE_PROMPTS and not files
        
        self.anim.set_state("thinking")
        self.status_bar.set_state_thinking()

        threading.Thread(
            target=self._bg_process,
            args=(prompt_text, is_simple),
            daemon=True,
        ).start()

    def _check_cloud_privacy(self, text: str) -> bool:
        if not self.agent:
            return False

        sensitive_keywords = [
            "password", "passcode", "credit card", "debit card", "cvv",
            "ssn", "social security", "passport", "bank account", "pin number",
            "medical record", "tax id", "aadhaar", "pan card", "private key", "secret key"
        ]
        has_sensitive = any(kw in text.lower() for kw in sensitive_keywords)
        current_model = getattr(self.agent.llm, "active_cloud_model", None) or getattr(self.agent.llm, "ollama_model", "gemma3")
        is_cloud = "gemini" in current_model.lower() or "gpt" in current_model.lower()

        if has_sensitive and is_cloud:
            self.chat.add_system_notice(
                "🔒 Privacy Notice: Personal/sensitive info detected in prompt. "
                "Switched to local model (gemma3) to process on-device for security."
            )
            self.agent.llm.set_model("gemma3")
            self._update_all_model_displays("gemma3", "LOCAL (PRIVACY GUARD)")
            return True
        return False

    def _bg_process(self, prompt: str, is_simple: bool) -> None:
        """Process reasoning. Show thinking indicator ONLY if latency exceeds 1.5s."""
        think_w = None
        streaming_started = False
        time_started = time.time()

        if not is_simple:
            def _think_timer():
                nonlocal think_w, streaming_started
                time.sleep(1.5)
                if not streaming_started and self._current_panel == "chat":
                    self.q.put(("show_thinking", None))
            threading.Thread(target=_think_timer, daemon=True).start()

        try:
            response_text = self.agent.process(prompt)
            streaming_started = True

            elapsed_ms = (time.time() - time_started) * 1000

            # Extract actual model used from response text or LLM engine state
            model_used = None
            if "(via " in response_text and response_text.rstrip().endswith(")"):
                try:
                    via_part = response_text.rstrip().rsplit("(via ", 1)[1].rstrip(")")
                    if via_part:
                        model_used = via_part
                except Exception:
                    pass

            if not model_used and self.agent and hasattr(self.agent, "llm"):
                model_used = getattr(self.agent.llm, "active_cloud_model", None) or getattr(self.agent.llm, "ollama_model", "gemma3")

            self.q.put(("response", {
                "text":       response_text,
                "elapsed_ms": elapsed_ms,
                "model":      model_used or "gemma3",
            }))
        except Exception as ex:
            streaming_started = True
            import traceback
            self.q.put(("error", f"{ex}\n{traceback.format_exc()}"))

    # ═════════════════════════════════════════════════════════════════════════
    # POLL LOOP
    # ═════════════════════════════════════════════════════════════════════════
    def _poll(self) -> None:
        try:
            while True:
                msg_type, payload = self.q.get_nowait()

                if msg_type == "agent_ready":
                    self._agent_ready(payload)

                elif msg_type == "agent_error":
                    self.anim.set_state("error")
                    self.status_bar.set_state_error()
                    self.chat.add_error_card("Agent Load Failure", payload, "Reinstall requirements or serve Ollama.")

                elif msg_type == "show_thinking":
                    if not self.chat._think_w:
                        self.chat.show_thinking()

                elif msg_type == "response":
                    self._start_streaming_reply(payload)

                elif msg_type == "error":
                    self.chat.hide_thinking()
                    self.anim.set_state("error")
                    self.status_bar.set_state_error()
                    self.chat.add_error_card("Execution Error", payload.split("\n")[0], "Verify your connection or prompt structure.")

                elif msg_type == "voice":
                    self.inp.populate_voice_text(payload)
                    self.anim.set_state("idle")

                elif msg_type == "reminder":
                    self.chat.add_system_notice(f"🔔 {payload}")

        except queue.Empty:
            pass
        self.root.after(50, self._poll)

    def _on_payment_authorize(self, intent_id: str) -> None:
        """User clicked Authorize Payment in UI card."""
        if not self.agent or not hasattr(self.agent, "payments"):
            self.chat.add_system_notice("⚠ Payment service unavailable.")
            return

        def _bg_auth():
            import uuid, hmac, hashlib
            auth_res = self.agent.payments.execute_tool_call("authorize_payment", {
                "intent_id": intent_id,
                "user_confirm": True
            })
            if not auth_res.get("success"):
                self.root.after(0, lambda: self.chat.add_payment_result_card({
                    "success": False,
                    "message": auth_res.get("message", "Authorization failed")
                }))
                return

            order_res = self.agent.payments.execute_tool_call("create_order", {
                "intent_id": intent_id,
                "mock": True
            })
            if not order_res.get("success"):
                self.root.after(0, lambda: self.chat.add_payment_result_card({
                    "success": False,
                    "message": order_res.get("message", "Order creation failed")
                }))
                return

            order_data = order_res.get("data", {}).get("order", {})
            order_id = order_data.get("order_id", "")

            payment_id = f"pay_{uuid.uuid4().hex[:14]}"
            secret = self.agent.payments.tool.config.key_secret or "mock_secret"
            sig = hmac.new(secret.encode("utf-8"), f"{order_id}|{payment_id}".encode("utf-8"), hashlib.sha256).hexdigest()

            verify_res = self.agent.payments.execute_tool_call("verify_payment", {
                "intent_id": intent_id,
                "payment_id": payment_id,
                "order_id": order_id,
                "signature": sig
            })

            if verify_res.get("success"):
                try:
                    from core.commerce.commerce_memory import CommerceMemoryRecorder
                    from core.commerce.commerce_models import CommerceContext, RecommendationResult, CostBreakdown, ProductCandidate, CommerceIntent, CommerceIntentCategory
                    dummy_cand = ProductCandidate("cand_verified", order_data.get("description", "Purchased Item"), "", order_data.get("amount", 0)/100.0, "Razorpay Merchant")
                    dummy_ctx = CommerceContext(
                        commerce_id="verified_comm",
                        intent=CommerceIntent("", CommerceIntentCategory.PURCHASE_REQUEST, "Item"),
                        recommendation=RecommendationResult(dummy_cand, "User authorized transaction"),
                        cost=CostBreakdown(dummy_cand.price_inr)
                    )
                    CommerceMemoryRecorder.record_transaction(dummy_ctx)
                except Exception:
                    pass

            self.root.after(0, lambda: self.chat.add_payment_result_card(verify_res.get("data", verify_res)))

        threading.Thread(target=_bg_auth, daemon=True).start()

    def _on_payment_cancel(self, intent_id: str) -> None:
        """User clicked Cancel in UI card."""
        if self.agent and hasattr(self.agent, "payments"):
            self.agent.payments.execute_tool_call("cancel_payment", {
                "intent_id": intent_id,
                "reason": "Cancelled by user via UI"
            })

    def _start_streaming_reply(self, data: dict) -> None:
        """Stream reply characters smoothly in main thread."""
        self.chat.hide_thinking()
        
        model = data.get("model") or getattr(self.agent.llm, "active_cloud_model", None) or getattr(self.agent.llm, "ollama_model", "gemma3")
        elapsed_ms = data.get("elapsed_ms", 0)
        text = data.get("text", "")

        if text.startswith("SCREEN_PERMISSION_REQUIRED_JSON:"):
            import json
            raw_json = text[len("SCREEN_PERMISSION_REQUIRED_JSON:"):].strip()
            try:
                perm_payload = json.loads(raw_json)
                def _on_perm_decision(choice):
                    def _bg_decision():
                        res = self.agent.process(choice)
                        self.q.put(("response", {"text": res, "elapsed_ms": 100, "model": model}))
                    threading.Thread(target=_bg_decision, daemon=True).start()

                self.chat.add_screen_permission_card(perm_payload, on_decision=_on_perm_decision)
                self.anim.set_state("idle")
                self.status_bar.set_state_ready()
                return
            except Exception as ex:
                log.error("Failed to parse screen permission JSON: %s", ex)

        if text.startswith("COMMERCE_INTENT_JSON:") or text.startswith("PAYMENT_INTENT_JSON:"):
            import json
            prefix = "COMMERCE_INTENT_JSON:" if text.startswith("COMMERCE_INTENT_JSON:") else "PAYMENT_INTENT_JSON:"
            try:
                raw_json = text[len(prefix):].strip()
                comm_res = json.loads(raw_json)
                prep_res = comm_res.get("payment_prepared") or comm_res
                intent_data = prep_res.get("data", {})
                self.chat.add_payment_transaction_card(
                    intent_data,
                    on_authorize=self._on_payment_authorize,
                    on_cancel=self._on_payment_cancel
                )
                self.anim.set_state("idle")
                self.status_bar.set_state_ready()
                return
            except Exception as ex:
                log.error("Failed to parse commerce intent JSON: %s", ex)

        card, txt, lbl_m = self.chat.add_streaming_helios_message()

        def _stream_tick(idx=0):
            if not txt.winfo_exists():
                return
            if idx < len(text):
                chunk = text[:idx+3]
                self.chat.update_streaming_content(txt, lbl_m, chunk)
                self.root.after(20, lambda: _stream_tick(idx + 3))
            else:
                self.chat.update_streaming_content(txt, lbl_m, text, {
                    "model": model,
                    "elapsed_ms": elapsed_ms
                })
                # Re-add final binds
                self.chat._cards_registry[-1]["text_content"] = text
                self.chat._cards_registry[-1]["type"] = "assistant"
                self.chat._on_theme_changed()

                self.anim.set_state("success")
                self.root.after(2000, lambda: self.anim.set_state("idle"))
                
                mode_str = "AUTO" if getattr(self, "_auto_route", True) else "MANUAL"
                self._update_all_model_displays(model, mode_str)
                self.status_bar.update(model=model, mode=mode_str, latency=f"{elapsed_ms:.0f}", state="Ready")
                self.status_bar.set_state_ready()

                # Activity & Diagnostics live data binding
                self._action_count = getattr(self, "_action_count", 0) + 1
                is_cloud = bool("gemini" in model.lower() or "gpt" in model.lower())
                self.diag_p.record_latency(elapsed_ms)
                self.diag_p.update_session(actions=self._action_count, verified=self._action_count, failed=0, state="idle", state_label="Ready")
                self.diag_p.update_llm(model=model, latency_ms=elapsed_ms, requests=self._action_count, is_local=not is_cloud)
                self.diag_p.add_activity_log(f"Processed: '{text[:30]}...' via {model} ({elapsed_ms:.0f}ms)")

        _stream_tick(0)

    # ═════════════════════════════════════════════════════════════════════════
    # DELEGATES
    # ═════════════════════════════════════════════════════════════════════════
    def _get_clipboard_text(self) -> str:
        try:
            return self.root.clipboard_get()
        except Exception:
            return ""

    def _insert_home_action(self, cmd_text: str) -> None:
        self.inp.entry.delete(0, tk.END)
        self.inp.entry.insert(0, cmd_text)
        self.inp.entry.configure(fg=C.FG_1)
        self.inp._is_ph = False
        self.inp.entry.focus_set()

    def _trigger_file_selection(self) -> None:
        self.inp._pick_files()

    def _edit_command_entry(self, e) -> None:
        txt = self._get_clipboard_text()
        self._insert_home_action(txt)

    def _save_agent_note(self, e) -> None:
        text = self._get_clipboard_text()
        if self.agent:
            try:
                self.agent.notes.add(text[:30], text)
                self.chat.add_system_notice("Note saved successfully.")
            except Exception as ex:
                self.chat.add_system_notice(f"Failed to save note: {ex}")

    def _regenerate_last(self) -> None:
        if self.agent:
            hist = self.agent.history.messages
            user_queries = [m for m in hist if m.get("role") == "user"]
            if user_queries:
                self._on_send(user_queries[-1]["content"], [])

    # ═════════════════════════════════════════════════════════════════════════
    # GLOBAL SEARCH & COMMAND PALETTE
    # ═════════════════════════════════════════════════════════════════════════
    def _open_global_search(self) -> None:
        if hasattr(self, "_search_win") and self._search_win.winfo_exists():
            self._search_win.destroy()
            return

        win = tk.Toplevel(self.root)
        self._search_win = win
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=C.BG_C2)

        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        pw, ph = 340, 400
        win.geometry(f"{pw}x{ph}+{rx + (WT.WIDTH - pw)//2}+{ry + 80}")
        win.attributes("-alpha", 0.98)

        tk.Label(win, text="Global Search (Files, Settings, History)",
                 font=(F._PRIMARY, F.SM, "bold"),
                 bg=C.BG_C2, fg=C.FG_1, pady=8).pack(fill="x")

        sv = tk.StringVar()
        entry = tk.Entry(win, textvariable=sv, font=(F._FALLBACK, F.MD),
                         bg=C.BG_INPUT, fg=C.FG_1, relief="flat", bd=6, insertbackground=C.BLUE)
        entry.pack(fill="x", padx=8, pady=(0, 4))
        entry.focus_set()

        tk.Frame(win, bg=C.BORDER, height=1).pack(fill="x")

        list_frame = tk.Frame(win, bg=C.BG_C2)
        list_frame.pack(fill="both", expand=True, padx=4, pady=4)

        def _search(*a):
            q = sv.get().lower().strip()
            for w in list_frame.winfo_children():
                w.destroy()

            results = []
            
            # History
            if self.agent:
                for s in (self.agent.history.get_all() or []):
                    if not q or q in s.get("title", "").lower():
                        results.append((f"💬 History: {s.get('title')}", lambda sid=s.get("id"): (self._on_load_session(sid), win.destroy())))
            
            # Settings
            settings_opts = [
                ("⚙ Action: Toggle Light Mode", lambda: (ThemeManager.set_mode("light", self.root), win.destroy())),
                ("⚙ Action: Toggle Dark Mode",  lambda: (ThemeManager.set_mode("dark", self.root), win.destroy())),
                ("⚙ Action: Toggle System Theme", lambda: (ThemeManager.set_mode("system", self.root), win.destroy())),
                ("⚙ Page: Open Diagnostics",     lambda: (self._on_nav("diagnostics"), win.destroy())),
                ("⚙ Page: Open Settings Drawer",  lambda: (self._toggle_settings(), win.destroy())),
            ]
            for label, cb in settings_opts:
                if not q or q in label.lower():
                    results.append((label, cb))

            # Models
            for m in _MODEL_CATALOG:
                if not q or q in m["name"].lower():
                    results.append((f"▦ Model: {m['name']} ({m['provider']})", lambda mid=m["id"]: (self._on_model_select(mid), win.destroy())))

            for label, cb in results[:8]:
                self._search_item(list_frame, label, cb)

        sv.trace_add("write", _search)
        _search()

        win.bind("<Escape>", lambda e: win.destroy())

    def _search_item(self, parent: tk.Widget, label: str, cb: callable) -> None:
        btn = tk.Label(parent, text=f"  {label}", font=(F._FALLBACK, F.SM),
                       bg=C.BG_C2, fg=C.FG_2, anchor="w", cursor="hand2", pady=6)
        btn.pack(fill="x")

        def enter(e): btn.configure(bg=C.BG_HOVER, fg=C.FG_1)
        def leave(e): btn.configure(bg=C.BG_C2, fg=C.FG_2)
        btn.bind("<Enter>", enter)
        btn.bind("<Leave>", leave)
        btn.bind("<ButtonRelease-1>", lambda e: cb())

    # ═════════════════════════════════════════════════════════════════════════
    # COMMAND PALETTE (Ctrl+K)
    # ═════════════════════════════════════════════════════════════════════════
    def _open_cmd_palette(self) -> None:
        if hasattr(self, "_palette") and self._palette.winfo_exists():
            self._palette.destroy()
            return

        pal = tk.Toplevel(self.root)
        self._palette = pal
        pal.overrideredirect(True)
        pal.attributes("-topmost", True)
        pal.configure(bg=C.BG_C2)

        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        pw, ph = 320, 380
        pal.geometry(f"{pw}x{ph}+{rx + (WT.WIDTH - pw)//2}+{ry + 80}")
        pal.attributes("-alpha", 0.98)

        tk.Label(pal, text="Command Palette",
                 font=(F._PRIMARY, F.SM, "bold"),
                 bg=C.BG_C2, fg=C.FG_1, pady=8).pack(fill="x", padx=12)

        sv = tk.StringVar()
        se = tk.Entry(pal, textvariable=sv, font=(F._FALLBACK, F.MD),
                      bg=C.BG_INPUT, fg=C.FG_1, relief="flat", bd=6, insertbackground=C.BLUE)
        se.insert(0, "Search commands…")
        se.pack(fill="x", padx=8, pady=(0, 4))
        se.focus_set()

        tk.Frame(pal, bg=C.BORDER, height=1).pack(fill="x")

        cmds = [
            ("◎  New Chat",            self._on_new_session),
            ("◎  Switch to Chat",      lambda: self._on_nav("chat")),
            ("▦  Models",              lambda: self._on_nav("models")),
            ("≡  History",             lambda: self._on_nav("history")),
            ("✦  Diagnostics",         lambda: self._on_nav("diagnostics")),
            ("⚙  Settings",            self._toggle_settings),
            ("✕  Close Window",        self._on_close),
        ]

        list_frame = tk.Frame(pal, bg=C.BG_C2)
        list_frame.pack(fill="both", expand=True, padx=4, pady=4)

        def _filter(*a):
            q = sv.get().lower()
            for w in list_frame.winfo_children():
                w.destroy()
            for label, cmd in cmds:
                if not q or q in label.lower() or "search" in q:
                    self._pal_item(list_frame, label, cmd, pal)

        sv.trace_add("write", _filter)
        _filter()

        pal.bind("<Escape>", lambda e: pal.destroy())

    def _pal_item(self, parent: tk.Widget, label: str, cmd: callable, pal: tk.Toplevel) -> None:
        btn = tk.Label(parent, text=f"  {label}", font=(F._FALLBACK, F.SM),
                       bg=C.BG_C2, fg=C.FG_2, anchor="w", cursor="hand2", pady=6)
        btn.pack(fill="x")

        def enter(e): btn.configure(bg=C.BG_HOVER, fg=C.FG_1)
        def leave(e): btn.configure(bg=C.BG_C2, fg=C.FG_2)
        def click(e):
            pal.destroy()
            cmd()

        btn.bind("<Enter>", enter)
        btn.bind("<Leave>", leave)
        btn.bind("<ButtonRelease-1>", click)

    # ═════════════════════════════════════════════════════════════════════════
    # DELEGATES & ACTIONS
    # ═════════════════════════════════════════════════════════════════════════
    def _toggle_settings(self) -> None:
        self.settings_drawer.toggle()

    def _on_voice_result(self, text: str) -> None:
        self.q.put(("voice", text))

    def _on_nav(self, key: str) -> None:
        if key == "settings":
            self._toggle_settings()
            return
        if hasattr(self, "settings_drawer") and self.settings_drawer._visible:
            self.settings_drawer.close_()
        self._show_panel(key)
        if key == "routing":
            self.routing_p.refresh()
        elif key == "history":
            self.history_p.refresh(self.agent)
        elif key in ("diagnostics", "activity"):
            self._sync_activity_telemetry()
            self.diag_p.refresh()
        elif key == "desktop":
            self.desktop_p.refresh()

    def _sync_activity_telemetry(self) -> None:
        if not hasattr(self, "diag_p"):
            return
        actions = getattr(self, "_action_count", 0)
        curr_model = getattr(self, "_active_model", "gemma3")
        is_cloud = bool("gemini" in curr_model.lower() or "gpt" in curr_model.lower())
        
        self.diag_p.update_session(actions=actions, verified=actions, failed=0, state="idle", state_label="Ready")
        self.diag_p.update_llm(model=curr_model, requests=actions, is_local=not is_cloud)
        
        try:
            from ui.desktop_panel import _get_active_window_title
            curr_app = _get_active_window_title()
            self.diag_p.update_screen(app_name=curr_app, is_local=True)
        except Exception:
            pass

    def _on_load_session(self, session_id: str) -> None:
        if not self.agent or not session_id:
            return
        try:
            msgs = self.agent.history.load(session_id)
            self.chat.clear()
            for m in (msgs or []):
                if m.get("role") == "user":
                    self.chat.add_user_message(m.get("content", ""))
                else:
                    self.chat.add_helios_message(m.get("content", ""))
            self._show_panel("chat")
            self.nav.set_active("chat")
        except Exception as ex:
            self.chat.add_system_notice(f"Failed to load: {ex}")

    def _on_new_session(self) -> None:
        if self.agent:
            try:
                from modules.chat_history import ChatHistory
                self.agent.history = ChatHistory()
            except Exception:
                pass
        self.chat.show_home_screen()
        self._show_panel("chat")
        self.nav.set_active("chat")
        SoundManager.model_switch()

    def _on_clear_history(self) -> None:
        if self.agent:
            try:
                self.agent.history.clear_all()
            except Exception:
                pass
        self.history_p.refresh(self.agent)
        if self.chat._home_view:
            self.chat._home_view.refresh(self.agent)

    def _on_model_select(self, model_id: str) -> None:
        if not self.agent:
            return
        try:
            self.agent.llm.set_model(model_id)
            if not getattr(self, "_auto_route", True):
                is_cloud = "gemini" in model_id.lower() or "gpt" in model_id.lower()
                self.agent.llm.set_mode("online" if is_cloud else "offline")
        except Exception:
            pass
        mode_str = "AUTO" if getattr(self, "_auto_route", True) else "MANUAL"
        self._update_all_model_displays(model_id, mode_str)
        SoundManager.model_switch()

    # ═════════════════════════════════════════════════════════════════════════
    # SETTINGS
    # ═════════════════════════════════════════════════════════════════════════
    def _load_settings(self) -> dict:
        try:
            if _SETTINGS_FILE.exists():
                return json.loads(_SETTINGS_FILE.read_text())
        except Exception:
            pass
        return {
            "mode": "auto",
            "language": "en-IN",
            "auto_scroll": True,
            "theme_mode": "dark",
            "reduced_motion": False,
            "high_contrast": False,
            "font_scale": "Normal",
            "sound": True,
            "voice_lang": "en-IN",
            "save_diagnostics": True,
            "save_log": True,
            "routing_warnings": True,
            "developer_mode": False
        }

    def _save_settings(self, data: dict) -> None:
        self._settings.update(data)
        try:
            _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            _SETTINGS_FILE.write_text(json.dumps(self._settings, indent=2))
        except Exception:
            pass
        
        # Apply theme with smooth transitions
        ThemeManager.set_mode(self._settings.get("theme_mode", "dark"), self.root)
        SoundManager.mute(not self._settings.get("sound", True))
        
        self._dev_mode_changed(self._settings.get("developer_mode", False))

    def _build_file_tags(self, files: list[str]) -> str:
        tags = []
        for path_str in files:
            path = Path(path_str)
            if not path.exists():
                tags.append(f"[ATTACHED FILE: {path_str} (File Not Found)]")
                continue

            ext = path.suffix.lower()
            content = ""

            if ext in {".docx", ".doc"}:
                try:
                    import docx
                    doc = docx.Document(str(path))
                    content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                except Exception as e:
                    content = f"Could not read DOCX content: {e}"

            elif ext == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(path))
                    content = "\n".join(page.extract_text() or "" for page in reader.pages)
                except Exception:
                    try:
                        import PyPDF2
                        reader = PyPDF2.PdfReader(str(path))
                        content = "\n".join(page.extract_text() or "" for page in reader.pages)
                    except Exception as e:
                        content = f"Could not read PDF content: {e}"

            elif ext in {".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json", ".csv", ".log"}:
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                except Exception as e:
                    content = f"Could not read text content: {e}"

            if content:
                if len(content) > 15000:
                    content = content[:15000] + "\n... [Content truncated for processing]"
                tags.append(f"[ATTACHED FILE CONTENT ({path.name})]:\n{content}")
            else:
                tags.append(f"[ATTACHED FILE: {path.name}]")

        return "\n\n".join(tags)

    def _on_status_msg(self, text: str) -> None:
        self.status_bar.update(state=text)

    def _on_close(self) -> None:
        shutdown_manager.shutdown(
            agent_instance=self.agent,
            ui_anim_engine=getattr(self, "anim", None),
            ui_diag_panel=getattr(self, "diag_p", None)
        )
        self.root.destroy()

    def _on_minimize(self) -> None:
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = self._get_hwnd()
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 6) # SW_MINIMIZE
                    return
            except Exception:
                pass
        self.root.iconify()

    def _get_work_area(self) -> tuple[int, int, int, int]:
        if sys.platform == "win32":
            try:
                import ctypes
                class RECT(ctypes.Structure):
                    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
                rect = RECT()
                ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                return rect.left, rect.top, w, h
            except Exception:
                pass
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        return 0, 0, sw, sh - 40

    def _on_maximize(self) -> None:
        if getattr(self, "_is_maximized", False):
            self._is_maximized = False
            nw = getattr(self, "_normal_w", WT.WIDTH)
            nh = getattr(self, "_normal_h", WT.HEIGHT)
            nx = getattr(self, "_normal_x", 100)
            ny = getattr(self, "_normal_y", 100)
            self.root.geometry(f"{nw}x{nh}+{nx}+{ny}")
            if hasattr(self, "header"):
                self.header.set_maximized_state(False)
        else:
            self._normal_w = self.root.winfo_width()
            self._normal_h = self.root.winfo_height()
            self._normal_x = self.root.winfo_x()
            self._normal_y = self.root.winfo_y()
            self._is_maximized = True

            x, y, w, h = self._get_work_area()
            self.root.geometry(f"{w}x{h}+{x}+{y}")
            if hasattr(self, "header"):
                self.header.set_maximized_state(True)

    def _set_floating_mode(self) -> None:
        """Minimizes window to small floating overlay mode for web/desktop searches."""
        self._is_maximized = False
        try:
            self.root.state("normal")
        except Exception:
            pass
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 420, 700
        x = sw - w - 20
        y = sh - h - 60
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _on_escape(self) -> None:
        if hasattr(self, "_palette") and self._palette.winfo_exists():
            self._palette.destroy()
        elif hasattr(self, "_search_win") and self._search_win.winfo_exists():
            self._search_win.destroy()
        elif self.settings_drawer._visible:
            self.settings_drawer.close_()

    def _drag_start(self, e: tk.Event) -> None:
        self._drag_sx = e.x_root - self.root.winfo_rootx()
        self._drag_sy = e.y_root - self.root.winfo_rooty()

    def _drag_do(self, e: tk.Event) -> None:
        if self._resize_active or self._resize_dir:
            return
        x = e.x_root - self._drag_sx
        y = e.y_root - self._drag_sy
        
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            w = self.root.winfo_width()
            y = max(0, min(y, sh - 80))
            x = max(100 - w, min(x, sw - 100))
        except Exception:
            pass
            
        self.root.geometry(f"+{x}+{y}")
        self._save_window_geometry()

    def _drag_end(self, e: tk.Event) -> None:
        pass

    # ─────────────────────────────────────────────────────────────────────────
    # 8-DIRECTIONAL RESIZING CONTROLLERS
    # ─────────────────────────────────────────────────────────────────────────
    def _on_root_motion(self, e: tk.Event) -> None:
        if self._resize_active:
            return
        try:
            rx = e.x_root - self.root.winfo_rootx()
            ry = e.y_root - self.root.winfo_rooty()
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            
            border = 6
            n = ry < border
            s = ry > h - border
            w_edge = rx < border
            e_edge = rx > w - border
            
            direction = ""
            if n: direction += "n"
            elif s: direction += "s"
            if w_edge: direction += "w"
            elif e_edge: direction += "e"
            
            self._resize_dir = direction
            
            if direction in ("nw", "se"):
                cursor = "size_nw_se"
            elif direction in ("ne", "sw"):
                cursor = "size_ne_sw"
            elif direction in ("n", "s"):
                cursor = "sb_v_double_arrow"
            elif direction in ("w", "e"):
                cursor = "sb_h_double_arrow"
            else:
                cursor = ""
                
            self.root.config(cursor=cursor)
        except Exception:
            pass

    def _on_root_click(self, e: tk.Event) -> None:
        if self._resize_dir:
            self._resize_active = True
            self._resize_start_w = self.root.winfo_width()
            self._resize_start_h = self.root.winfo_height()
            self._resize_start_x = e.x_root
            self._resize_start_y = e.y_root
            self._resize_start_wx = self.root.winfo_x()
            self._resize_start_wy = self.root.winfo_y()

    def _on_root_drag(self, e: tk.Event) -> None:
        if not self._resize_active or not self._resize_dir:
            return
        try:
            dx = e.x_root - self._resize_start_x
            dy = e.y_root - self._resize_start_y
            
            nw = self._resize_start_w
            nh = self._resize_start_h
            nx = self._resize_start_wx
            ny = self._resize_start_wy
            
            if "e" in self._resize_dir:
                nw = max(WT.MIN_W, self._resize_start_w + dx)
            elif "w" in self._resize_dir:
                val = self._resize_start_w - dx
                if val >= WT.MIN_W:
                    nw = val
                    nx = self._resize_start_wx + dx
                    
            if "s" in self._resize_dir:
                nh = max(WT.MIN_H, self._resize_start_h + dy)
            elif "n" in self._resize_dir:
                val = self._resize_start_h - dy
                if val >= WT.MIN_H:
                    nh = val
                    ny = self._resize_start_wy + dy
                    
            self.root.geometry(f"{nw}x{nh}+{nx}+{ny}")
            self._save_window_geometry()
        except Exception:
            pass

    def _on_root_release(self, e: tk.Event) -> None:
        self._resize_active = False
        self._resize_dir = ""
        try:
            self.root.config(cursor="")
        except Exception:
            pass


if __name__ == "__main__":
    HELIOSApp()