"""
ui/status_bar.py — HELIOS Status Bar Component
===============================================
Material status footer bar with model and state telemetry updating.
"""

from __future__ import annotations
import tkinter as tk

TEXT_PRIMARY   = "#F4F7FF"
TEXT_MUTED     = "#8994AA"
TEXT_EMERALD   = "#34D399"
TEXT_AMBER     = "#FBBF24"
TEXT_ERR       = "#EF4444"
GLASS_BORDER   = "#233366"


class StatusBar:
    """Status bar footer displaying connection state and version info."""

    def __init__(self, parent: tk.Widget) -> None:
        self.frame = tk.Frame(parent, bg="#060914", height=24)
        self.frame.pack_propagate(False)

        self._build()

    def _build(self) -> None:
        sb = self.frame
        tk.Frame(sb, bg=GLASS_BORDER, height=1).pack(fill="x", side="top")

        self.lbl_dot = tk.Label(sb, text="  ● READY", font=("Segoe UI", 8, "bold"), bg="#060914", fg=TEXT_EMERALD)
        self.lbl_dot.pack(side="left")

        self.lbl_info = tk.Label(sb, text="  |  Privacy Guard Active  ·  Offline Mode", font=("Segoe UI", 8), bg="#060914", fg=TEXT_MUTED)
        self.lbl_info.pack(side="left")

        self._lbl_model = tk.Label(sb, text="Gemma 3 4B", font=("Segoe UI", 8), bg="#060914", fg=TEXT_MUTED)

        self.resize_grip = tk.Label(sb, text="◢", font=("Segoe UI", 9), bg="#060914", fg=TEXT_MUTED, cursor="sb_h_double_arrow")
        self.resize_grip.pack(side="right", padx=(0, 2))

        self.lbl_ver = tk.Label(sb, text="HELIOS v4.0  ", font=("Segoe UI", 8), bg="#060914", fg=TEXT_MUTED)
        self.lbl_ver.pack(side="right")

    def update(self, model: str = None, mode: str = None, memory: str = None, latency: str = None, state: str = "Ready") -> None:
        if model:
            self._lbl_model.configure(text=model)
        if state:
            self.lbl_dot.configure(text=f"  ● {state.upper()}")

    def set_state(self, state: str, message: str = "") -> None:
        self.lbl_dot.configure(text=f"  ● {state.upper()}")

    def set_state_thinking(self, text: str = "Thinking…") -> None:
        self.lbl_dot.configure(text="  ● THINKING", fg=TEXT_AMBER)

    def set_state_error(self, text: str = "Error") -> None:
        self.lbl_dot.configure(text="  ● ERROR", fg=TEXT_ERR)

    def set_state_ready(self) -> None:
        self.lbl_dot.configure(text="  ● READY", fg=TEXT_EMERALD)

    def set_thinking(self, text: str = "Thinking…") -> None:
        self.set_state_thinking(text)

    def set_idle(self) -> None:
        self.set_state_ready()
