"""
core/system/shutdown.py — HELIOS Shutdown Manager
===================================================
Provides idempotent resource release, background task cancellation,
scheduler shutdown, thread pool termination, and log flushing.
"""

import logging
import threading
from .paths import paths_manager

log = logging.getLogger("helios.shutdown")


class ShutdownManager:
    """Manages application graceful exit procedures."""

    def __init__(self) -> None:
        self._shutdown_executed = False
        self._lock = threading.Lock()

    def shutdown(self, agent_instance=None, ui_anim_engine=None, ui_diag_panel=None) -> None:
        """Idempotent shutdown handler."""
        with self._lock:
            if self._shutdown_executed:
                return
            self._shutdown_executed = True

        log.info("Initiating HELIOS application shutdown sequence...")

        # 1. Stop UI Animation & Diagnostics Threads
        if ui_anim_engine and hasattr(ui_anim_engine, "stop"):
            try:
                ui_anim_engine.stop()
            except Exception as e:
                log.warning(f"Error stopping animation engine: {e}")

        if ui_diag_panel and hasattr(ui_diag_panel, "stop"):
            try:
                ui_diag_panel.stop()
            except Exception as e:
                log.warning(f"Error stopping diagnostics panel: {e}")

        # 2. Stop HELIOS Agent Subsystems (APScheduler, Voice, etc.)
        if agent_instance:
            try:
                if hasattr(agent_instance, "shutdown"):
                    agent_instance.shutdown()
                elif hasattr(agent_instance, "scheduler") and hasattr(agent_instance.scheduler, "shutdown"):
                    agent_instance.scheduler.shutdown()
            except Exception as e:
                log.warning(f"Error terminating agent resources: {e}")

        # 3. Clean Temporary Files
        try:
            temp_dir = paths_manager.temp_dir
            for item in temp_dir.glob("*"):
                if item.is_file():
                    try:
                        item.unlink()
                    except Exception:
                        pass
        except Exception as e:
            log.warning(f"Error clearing temporary files: {e}")

        # 4. Flush File Log Handlers
        log.info("Flushing log buffers and exiting.")
        try:
            logging.shutdown()
        except Exception:
            pass


shutdown_manager = ShutdownManager()
