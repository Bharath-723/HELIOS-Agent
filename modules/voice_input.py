"""
HELIOS - Voice Input Module
============================
Non-blocking, thread-safe speech recognition.

Backends (tried in order):
  1. Google Speech-to-Text  (online, highest accuracy)
  2. Whisper via SpeechRecognition  (offline fallback, if openai-whisper installed)

Install dependencies once:
    pip install SpeechRecognition pyaudio

    # If pyaudio fails on Windows:
    pip install pipwin && pipwin install pyaudio

    # Optional offline Whisper backend:
    pip install openai-whisper

Usage in other modules:
    from modules.voice_input import VoiceInput, VoiceResult

    def handle(r: VoiceResult):
        if r.success:
            print("Heard:", r.text, "via", r.engine)
        else:
            print("Error:", r.error)

    vi = VoiceInput(language="en-IN", timeout=5, phrase_limit=12)
    vi.start(callback=handle)   # non-blocking — returns immediately
    # vi.stop()                 # can be called anytime to abort
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Callable, Optional

log = logging.getLogger("helios.voice")

# ── User-facing error strings ─────────────────────────────────────────────────
ERR_NO_SR     = ("SpeechRecognition not installed.\n"
                 "Fix:  pip install SpeechRecognition")
ERR_NO_AUDIO  = ("PyAudio not installed.\n"
                 "Fix:  pip install pyaudio\n"
                 "Windows:  pip install pipwin && pipwin install pyaudio")
ERR_NO_MIC    = "No microphone found — check your audio input device."
ERR_TIMEOUT   = "No speech detected (timeout). Please try again."
ERR_UNCLEAR   = "Could not understand audio. Please speak clearly and try again."
ERR_NETWORK   = ("Cannot reach Google Speech API — check internet connection.\n"
                 "Tip: install openai-whisper for offline transcription.")
ERR_STOPPED   = "Recording stopped."


# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class VoiceResult:
    """
    Passed to the caller callback after every listen attempt.

    Attributes
    ----------
    success : bool   — True if transcription succeeded
    text    : str    — transcribed text (empty on failure)
    error   : str    — human-readable error (empty on success)
    engine  : str    — backend used: "Google", "Whisper", ""
    """
    success: bool
    text:    str = ""
    error:   str = ""
    engine:  str = ""

    @classmethod
    def ok(cls, text: str, engine: str = "Google") -> "VoiceResult":
        return cls(success=True, text=text.strip(), engine=engine)

    @classmethod
    def fail(cls, error: str) -> "VoiceResult":
        return cls(success=False, error=error)


# ─────────────────────────────────────────────────────────────────────────────
class VoiceInput:
    """
    One-click voice capture and transcription.

    Parameters
    ----------
    language        : BCP-47 tag, e.g. "en-IN", "en-US", "hi-IN"
    timeout         : seconds to wait for speech to start before giving up
    phrase_limit    : max seconds of speech to capture per click
    energy_threshold: mic sensitivity (None = auto-calibrate on every click)
    prefer_offline  : try Whisper first, Google as fallback
    """

    def __init__(
        self,
        language:         str          = "en-IN",
        timeout:          int          = 5,
        phrase_limit:     int          = 12,
        energy_threshold: Optional[int] = None,
        prefer_offline:   bool         = False,
    ) -> None:
        self.language         = language
        self.timeout          = timeout
        self.phrase_limit     = phrase_limit
        self.energy_threshold = energy_threshold
        self.prefer_offline   = prefer_offline

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Pre-check imports so errors surface immediately in the UI
        self._sr_ok    = self._import_ok("speech_recognition")
        self._audio_ok = self._import_ok("pyaudio")

        if not self._sr_ok:
            log.warning("SpeechRecognition not installed.")
        if not self._audio_ok:
            log.warning("PyAudio not installed.")

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _import_ok(module_name: str) -> bool:
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

    @staticmethod
    def is_available() -> bool:
        """Return True only when both required libraries are importable."""
        try:
            import speech_recognition  # noqa: F401
            import pyaudio             # noqa: F401
            return True
        except ImportError:
            return False

    def ready_error(self) -> str:
        """Return a human-readable install hint, or '' if everything is OK."""
        if not self._sr_ok:
            return ERR_NO_SR
        if not self._audio_ok:
            return ERR_NO_AUDIO
        return ""

    # ── Public API ────────────────────────────────────────────────────────────
    def start(self, callback: Callable[[VoiceResult], None]) -> None:
        """
        Start listening in a background daemon thread.
        `callback` is invoked exactly once when recording + transcription end.
        Thread-safe — safe to call from the Tkinter event loop.
        """
        # Pre-flight checks
        err = self.ready_error()
        if err:
            callback(VoiceResult.fail(err))
            return

        # Prevent duplicate threads
        if self._thread and self._thread.is_alive():
            log.debug("start() ignored — thread already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._worker,
            args=(callback,),
            name="helios-voice",
            daemon=True,
        )
        self._thread.start()
        log.info("Voice thread started  lang=%s  timeout=%ds  limit=%ds",
                 self.language, self.timeout, self.phrase_limit)

    def stop(self) -> None:
        """
        Request early termination.
        The callback is still called once (with ERR_STOPPED or the
        partial result if transcription already finished).
        """
        log.info("Voice stop requested.")
        self._stop_event.set()

    # ── Worker (runs in daemon thread) ────────────────────────────────────────
    def _worker(self, callback: Callable[[VoiceResult], None]) -> None:
        """Calls callback exactly once, then exits."""
        try:
            result = self._run()
        except Exception as exc:
            log.error("Unexpected voice worker error: %s", exc, exc_info=True)
            result = VoiceResult.fail(f"Unexpected error: {exc}")
        callback(result)

    def _run(self) -> VoiceResult:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8    # silence that ends a phrase

        if self.energy_threshold is not None:
            recognizer.energy_threshold      = self.energy_threshold
            recognizer.dynamic_energy_threshold = False

        # ── Open microphone ───────────────────────────────────────────────
        try:
            mic = sr.Microphone()
        except OSError as exc:
            log.error("Microphone open error: %s", exc)
            return VoiceResult.fail(ERR_NO_MIC)
        except Exception as exc:
            log.error("Unexpected mic error: %s", exc)
            return VoiceResult.fail(f"Microphone error: {exc}")

        # ── Calibrate for ambient noise ───────────────────────────────────
        try:
            with mic as source:
                log.debug("Calibrating ambient noise (0.8 s)…")
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                log.debug("Calibrated — energy threshold: %.0f",
                          recognizer.energy_threshold)
        except Exception as exc:
            # Non-fatal — proceed with whatever threshold we have
            log.warning("Calibration skipped: %s", exc)

        # ── Capture audio ─────────────────────────────────────────────────
        audio = None
        try:
            with mic as source:
                log.info("Listening…  (timeout=%ds, phrase_limit=%ds)",
                         self.timeout, self.phrase_limit)
                audio = recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_limit,
                )
            log.info("Audio captured — %d raw bytes",
                     len(audio.get_raw_data()))
        except sr.WaitTimeoutError:
            log.info("Timeout — no speech detected.")
            return VoiceResult.fail(ERR_TIMEOUT)
        except OSError as exc:
            log.error("Mic read error: %s", exc)
            return VoiceResult.fail(f"Microphone read error: {exc}")
        except Exception as exc:
            log.error("Capture error: %s", exc, exc_info=True)
            return VoiceResult.fail(f"Capture error: {exc}")

        # Honour early stop
        if self._stop_event.is_set():
            log.info("Stop flag set — discarding captured audio.")
            return VoiceResult.fail(ERR_STOPPED)

        # ── Transcription ─────────────────────────────────────────────────
        if self.prefer_offline:
            r = self._whisper(audio)
            if r.success:
                return r
            log.info("Whisper failed (%s) — trying Google.", r.error)

        r = self._google(recognizer, audio)

        # Google failed → try Whisper as last resort
        if not r.success:
            log.info("Google failed (%s) — trying Whisper.", r.error)
            wr = self._whisper(audio)
            if wr.success:
                return wr

        return r

    # ── Google Speech-to-Text ─────────────────────────────────────────────────
    def _google(self, recognizer, audio) -> VoiceResult:
        import speech_recognition as sr
        try:
            text = recognizer.recognize_google(audio, language=self.language)
            log.info("Google STT → \"%s\"", text)
            return VoiceResult.ok(text, engine="Google")
        except sr.UnknownValueError:
            log.info("Google STT: audio unclear.")
            return VoiceResult.fail(ERR_UNCLEAR)
        except sr.RequestError as exc:
            log.error("Google STT network error: %s", exc)
            return VoiceResult.fail(f"{ERR_NETWORK}\nDetail: {exc}")
        except Exception as exc:
            log.error("Google STT unexpected: %s", exc, exc_info=True)
            return VoiceResult.fail(f"STT error: {exc}")

    # ── Whisper offline transcription ─────────────────────────────────────────
    def _whisper(self, audio) -> VoiceResult:
        """
        Uses speech_recognition's recognize_whisper() wrapper.
        Requires:  pip install openai-whisper
        Silently returns a failure VoiceResult if not installed.
        """
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            # language tag: "en-IN" → "en" for Whisper
            lang = self.language.split("-")[0]
            text = recognizer.recognize_whisper(
                audio,
                language=lang,
                model="base",           # tiny / base / small — trade speed for accuracy
            )
            log.info("Whisper STT → \"%s\"", text)
            return VoiceResult.ok(text, engine="Whisper (offline)")
        except ImportError:
            return VoiceResult.fail("openai-whisper not installed.")
        except Exception as exc:
            log.warning("Whisper STT failed: %s", exc)
            return VoiceResult.fail(f"Whisper error: {exc}")
