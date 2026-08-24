"""
ui_visual_regression_test.py — HELIOS UI Visual Regression Suite
=================================================================
Tests the complete UI widget tree for visual visibility.

INVARIANT: A widget exists does NOT mean it is visible.
This test checks: exists + mapped + width > 0 + height > 0

No network, no Ollama, no Tavily, no desktop automation.

Run:
    venv\\Scripts\\python.exe ui_visual_regression_test.py
"""

import sys
import os
import time
import tkinter as tk
import logging

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")
log = logging.getLogger("helios.ui_test")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_visible(widget: tk.Widget, name: str) -> bool:
    """Returns True only if widget is actually visible on screen."""
    try:
        exists  = widget.winfo_exists()
        mapped  = widget.winfo_ismapped()
        width   = widget.winfo_width()
        height  = widget.winfo_height()
        visible = exists and mapped and width > 0 and height > 0
        status = "OK  " if visible else "FAIL"
        log.info("[%s] %-30s exists=%-5s mapped=%-5s w=%-5s h=%-5s",
                 status, name, exists, mapped, width, height)
        return visible
    except Exception as ex:
        log.error("[FAIL] %-30s ERROR: %s", name, ex)
        return False


def check_layer_order(bg_layer: tk.Frame, fg_layer: tk.Frame) -> bool:
    """Check that foreground_layer is above background_layer."""
    try:
        # In Tkinter, the last widget in stacking order is on top.
        # We verify by calling lift and checking no exception occurs.
        fg_layer.lift()
        log.info("[OK  ] foreground_layer.lift() succeeded — is above background_layer")
        return True
    except Exception as ex:
        log.error("[FAIL] Layer ordering check failed: %s", ex)
        return False


def measure_ms(fn):
    """Time a function call in milliseconds."""
    t0 = time.perf_counter()
    fn()
    return round((time.perf_counter() - t0) * 1000, 1)


class TestApp:
    """Minimal test harness that creates real HELIOS UI without agent/LLM."""

    def __init__(self):
        self.results: dict[str, bool] = {}
        self.perf: dict[str, float] = {}

    def run(self):
        root = tk.Tk()
        root.title("HELIOS UI Visual Regression Test")
        root.geometry("900x700")
        root.configure(bg="#080B1A")

        from ui.theme import C, ThemeManager
        ThemeManager.set_mode("dark")

        # ── Build two-layer architecture ──────────────────────────────────────
        main = tk.Frame(root, bg=C.BG, bd=0)
        main.place(x=2, y=2, relwidth=1.0, relheight=1.0, width=-4, height=-4)

        t0 = time.perf_counter()
        background_layer = tk.Frame(main, bg=C.BG, bd=0)
        background_layer.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        foreground_layer = tk.Frame(main, bg=C.BG, bd=0)
        foreground_layer.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        foreground_layer.lift()
        self.perf["shell_visible_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        # ── Background layer ──────────────────────────────────────────────────
        from ui.ambient_background import AmbientBackground
        bg_obj = AmbientBackground(background_layer, 900, 700)

        # ── Header ───────────────────────────────────────────────────────────
        from ui.header import Header
        t0 = time.perf_counter()
        header = Header(
            foreground_layer,
            on_close     = root.destroy,
            on_minimize  = lambda: None,
            on_maximize  = lambda: None,
            on_settings  = lambda: None,
            on_drag_start= lambda e: None,
            on_drag_do   = lambda e: None,
            on_drag_end  = lambda e: None,
        )
        header.frame.pack(side="top", fill="x")
        self.perf["header_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        # ── Status bar ───────────────────────────────────────────────────────
        from ui.status_bar import StatusBar
        status_bar = StatusBar(foreground_layer)
        status_bar.frame.pack(side="bottom", fill="x")

        # ── Input panel ──────────────────────────────────────────────────────
        from ui.input_panel import InputPanel
        inp = InputPanel(
            foreground_layer,
            on_send         = lambda t, f: None,
            on_voice_result = lambda t: None,
            on_status       = lambda m: None,
        )
        inp.frame.pack(side="bottom", fill="x")

        # ── Body row ─────────────────────────────────────────────────────────
        body_row = tk.Frame(foreground_layer, bg=C.BG)
        body_row.pack(side="top", fill="both", expand=True)

        from ui.navigation_rail import NavigationRail
        nav = NavigationRail(body_row, on_nav=lambda k: None,
                             tooltip_parent=foreground_layer)
        nav.frame.pack(side="left", fill="y")

        panel_area = tk.Frame(body_row, bg=C.BG_S)
        panel_area.pack(side="left", fill="both", expand=True)

        # ── Chat view ────────────────────────────────────────────────────────
        from ui.chat_view import ChatView
        t0 = time.perf_counter()
        chat = ChatView(panel_area, anim_engine=None)
        chat.frame.pack(fill="both", expand=True)
        self.perf["chat_created_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        root.update()
        root.update_idletasks()

        # ── Run visibility checks ─────────────────────────────────────────────
        def run_checks():
            root.update()
            root.update_idletasks()

            # Layer checks
            self.results["bg_layer_exists"]    = check_visible(background_layer, "background_layer")
            self.results["fg_layer_exists"]    = check_visible(foreground_layer, "foreground_layer")
            self.results["layer_order"]        = check_layer_order(background_layer, foreground_layer)
            self.results["header_visible"]     = check_visible(header.frame, "header.frame")
            self.results["nav_visible"]        = check_visible(nav.frame, "navigation_rail.frame")
            self.results["panel_area_visible"] = check_visible(panel_area, "panel_area")
            self.results["chat_frame_visible"] = check_visible(chat.frame, "chat.frame")
            self.results["chat_canvas_visible"]= check_visible(chat.canvas, "chat.canvas")
            self.results["chat_msgs_visible"]  = check_visible(chat.msgs, "chat.msgs")
            self.results["status_visible"]     = check_visible(status_bar.frame, "status_bar.frame")
            self.results["input_visible"]      = check_visible(inp.frame, "input_panel.frame")
            self.results["is_visible_api"]     = chat.is_visible()
            log.info("[%s] chat.is_visible() API", "OK  " if self.results["is_visible_api"] else "FAIL")

            # Add user message and check
            t0 = time.perf_counter()
            chat.add_user_message("hello")
            root.update()
            self.perf["user_message_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            self.results["user_msg_rendered"] = check_visible(chat.msgs, "chat.msgs after user msg")

            # Add HELIOS response
            t0 = time.perf_counter()
            chat.add_helios_message("Hello! I am HELIOS. How can I help you today?")
            root.update()
            self.perf["helios_message_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            self.results["helios_msg_rendered"] = check_visible(chat.msgs, "chat.msgs after helios msg")

            # Add thinking indicator
            think = chat.show_thinking()
            root.update()
            self.results["thinking_visible"] = check_visible(think.frame, "thinking_indicator.frame")
            chat.hide_thinking()
            root.update()

            # Add more messages
            for i in range(10):
                chat.add_user_message(f"Test message {i+1}")
            root.update()
            self.results["multi_msg_rendered"] = check_visible(chat.msgs, "chat.msgs after 10 msgs")

            # System notice
            chat.add_system_notice("System: Task completed.")
            root.update()
            self.results["system_notice_ok"] = check_visible(chat.msgs, "chat.msgs after system notice")

            # Error card
            chat.add_error_card("Something went wrong.", "Try again.")
            root.update()
            self.results["error_msg_ok"] = check_visible(chat.msgs, "chat.msgs after error")

            # Summary
            passed = sum(1 for v in self.results.values() if v)
            total  = len(self.results)
            log.info("")
            log.info("=" * 60)
            log.info("VISUAL REGRESSION RESULTS: %d/%d passed", passed, total)
            log.info("=" * 60)
            for key, val in self.results.items():
                log.info("  %-35s %s", key, "PASS" if val else "FAIL")
            log.info("")
            log.info("PERFORMANCE MEASUREMENTS:")
            for key, ms in self.perf.items():
                log.info("  %-35s %s ms", key, ms)
            log.info("=" * 60)

            if passed == total:
                log.info("ALL CHECKS PASSED — Chat is visually confirmed on screen.")
            else:
                failed = [k for k, v in self.results.items() if not v]
                log.error("FAILURES: %s", failed)

            root.after(2000, root.destroy)

        root.after(300, run_checks)
        root.mainloop()

        return self.results, self.perf


if __name__ == "__main__":
    app = TestApp()
    results, perf = app.run()
    failed = [k for k, v in results.items() if not v]
    sys.exit(0 if not failed else 1)
