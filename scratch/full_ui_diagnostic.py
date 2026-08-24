"""
scratch/full_ui_diagnostic.py — HELIOS Full UI Diagnostic Telemetry Runner
==========================================================================
Launches HELIOSApp in a controlled test harness, captures object IDs, widget classes,
parent relationships, geometry, scrollregion, message pipelines, and stacking order.
"""

import sys
import time
import threading
import tkinter as tk
import logging

sys.path.insert(0, ".")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("helios.diagnostic")


def run_full_diagnostic():
    log.info("==================================================")
    log.info("STARTING HELIOS FULL UI DIAGNOSTIC RUNNER")
    log.info("==================================================")

    import helios_popup
    helios_popup.HELIOSApp._instance = None  # Clear instance guard

    app = helios_popup.HELIOSApp.__new__(helios_popup.HELIOSApp)
    
    # Initialize runtime
    from core.system import runtime_manager
    app.runtime_ctx = runtime_manager.initialize_runtime()
    app.root = tk.Tk()
    app.root.report_callback_exception = app._on_tkinter_error

    app.agent = None
    app.q = helios_popup.queue.Queue()
    app._current_panel = "chat"
    app._drag_sx = app._drag_sy = 0
    app._resize_w = app._resize_h = 0
    app._resize_x = app._resize_y = 0
    app._settings = app._load_settings()
    app._start_ts = time.time()
    app._auto_route = True

    from ui.theme import ThemeManager, C, W
    from ui.sound_manager import SoundManager
    from ui.ambient_background import AmbientBackground
    from ui.animation_engine import AnimationEngine

    ThemeManager.set_mode("dark")
    app._setup_window()

    app.bg = AmbientBackground(app.root, W.WIDTH, W.HEIGHT)
    app.anim = AnimationEngine(app.root, app.bg.canvas, W.WIDTH, W.HEIGHT)

    app._build_main_container()
    app._build_header()
    app._build_status_bar()
    app._build_input()
    app.inp.frame.pack_configure(side="bottom")
    app._build_content_area()
    app._build_panels()
    app._build_settings_drawer()

    app.root.update()

    # ── PHASE 1: TRACE CHAT UI CREATION & OBJECT IDS ───────────────────────────
    log.info("[UI INIT]")
    log.info(f"root: id={id(app.root)} class={app.root.__class__.__name__} parent=None mapped={app.root.winfo_ismapped()}")
    log.info(f"chat_container (panel_area): id={id(app.panel_area)} class={app.panel_area.__class__.__name__} parent={app.panel_area.master} mapped={app.panel_area.winfo_ismapped()}")
    log.info(f"chat.frame: id={id(app.chat.frame)} class={app.chat.frame.__class__.__name__} parent={app.chat.frame.master} mapped={app.chat.frame.winfo_ismapped()}")
    log.info(f"chat.canvas: id={id(app.chat.canvas)} class={app.chat.canvas.__class__.__name__} parent={app.chat.canvas.master} mapped={app.chat.canvas.winfo_ismapped()}")
    log.info(f"chat.msgs: id={id(app.chat.msgs)} class={app.chat.msgs.__class__.__name__} parent={app.chat.msgs.master} mapped={app.chat.msgs.winfo_ismapped()}")
    log.info(f"input: id={id(app.inp.frame)} class={app.inp.frame.__class__.__name__} parent={app.inp.frame.master} mapped={app.inp.frame.winfo_ismapped()}")
    log.info(f"status_bar: id={id(app.status_bar.frame)} class={app.status_bar.frame.__class__.__name__} parent={app.status_bar.frame.master} mapped={app.status_bar.frame.winfo_ismapped()}")

    # ── PHASE 2: CHECK GEOMETRY ─────────────────────────────────────────────
    log.info("[CHAT GEOMETRY]")
    log.info(f"chat.frame x={app.chat.frame.winfo_x()} y={app.chat.frame.winfo_y()} w={app.chat.frame.winfo_width()} h={app.chat.frame.winfo_height()} req_w={app.chat.frame.winfo_reqwidth()} req_h={app.chat.frame.winfo_reqheight()}")
    log.info(f"panel_area w={app.panel_area.winfo_width()} h={app.panel_area.winfo_height()}")
    log.info(f"canvas w={app.chat.canvas.winfo_width()} h={app.chat.canvas.winfo_height()}")
    log.info(f"msgs w={app.chat.msgs.winfo_width()} h={app.chat.msgs.winfo_height()}")

    # ── PHASE 3: STATIC TEST MESSAGE ─────────────────────────────────────────
    log.info("[PHASE 3 STATIC TEST MESSAGE]")
    app.chat.add_system_notice("HELIOS CHAT INITIALIZATION OK")
    app.root.update()

    log.info(f"msgs children count after static test: {len(app.chat.msgs.winfo_children())}")
    log.info(f"msgs req height: {app.chat.msgs.winfo_reqheight()}")

    # ── PHASE 6: CHECK CANVAS / SCROLLABLE IMPLEMENTATION ──────────────────────
    log.info("[CHAT CANVAS]")
    log.info(f"canvas_width={app.chat.canvas.winfo_width()} canvas_height={app.chat.canvas.winfo_height()}")
    log.info(f"scrollregion={app.chat.canvas.cget('scrollregion')}")
    log.info(f"window_items={app.chat.canvas.find_all()}")
    log.info(f"inner_frame_width={app.chat.msgs.winfo_width()} inner_frame_height={app.chat.msgs.winfo_height()}")

    # ── PHASE 8: CHECK FRAME STACKING / Z-ORDER ──────────────────────────────
    log.info("[CHAT CHILDREN]")
    for child in app.main.winfo_children():
        log.info(f"main child: {child.__class__.__name__} w={child.winfo_width()} h={child.winfo_height()} mapped={child.winfo_ismapped()}")
    for child in app.content_row.winfo_children():
        log.info(f"content_row child: {child.__class__.__name__} w={child.winfo_width()} h={child.winfo_height()} mapped={child.winfo_ismapped()}")
    for child in app.panel_area.winfo_children():
        log.info(f"panel_area child: {child.__class__.__name__} w={child.winfo_width()} h={child.winfo_height()} mapped={child.winfo_ismapped()}")

    # ── PHASE 9: CHECK UI THREAD ─────────────────────────────────────────────
    log.info("[UI THREAD]")
    log.info(f"main_thread={threading.main_thread().name} current_thread={threading.current_thread().name}")

    app.root.destroy()
    log.info("==================================================")
    log.info("FULL DIAGNOSTIC COMPLETED")
    log.info("==================================================")

if __name__ == "__main__":
    run_full_diagnostic()
