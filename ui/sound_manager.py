"""
ui/sound_manager.py — HELIOS Audio System
==========================================
Loads and plays the startup sound from assets/sounds/startup.wav.
If the file is missing or on non-Windows platforms, fails silently.
To prevent audio distraction, all other sounds during normal usage are disabled.
"""

from __future__ import annotations
import sys
import threading
from pathlib import Path


class SoundManager:
    """Manages HELIOS audio playback. All functions run asynchronously."""

    _muted: bool = False

    @classmethod
    def mute(cls, value: bool = True) -> None:
        cls._muted = value

    @classmethod
    def startup(cls) -> None:
        """
        Play assets/sounds/startup.wav if present.
        Place your preferred startup sound here:
        assets/sounds/startup.wav
        """
        if cls._muted:
            return
        if sys.platform != "win32":
            return

        sound_path = Path(__file__).parent.parent / "assets" / "sounds" / "startup.wav"
        if not sound_path.exists():
            return

        def _run():
            try:
                import winsound
                # Play asynchronous sound file
                winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

        threading.Thread(target=_run, daemon=True).start()

    # ── Suppressed helper sounds to prevent distraction during usage ─────────
    @classmethod
    def message_sent(cls) -> None: pass

    @classmethod
    def message_received(cls) -> None: pass

    @classmethod
    def thinking_done(cls) -> None: pass

    @classmethod
    def voice_activate(cls) -> None: pass

    @classmethod
    def voice_deactivate(cls) -> None: pass

    @classmethod
    def model_switch(cls) -> None: pass

    @classmethod
    def error(cls) -> None: pass

    @classmethod
    def success(cls) -> None: pass

    @classmethod
    def nav_switch(cls) -> None: pass

    @classmethod
    def toggle(cls) -> None: pass
