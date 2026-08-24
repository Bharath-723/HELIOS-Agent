"""
ui/camera_modal.py — ChatGPT-style In-App Camera Modal for HELIOS
==================================================================
Live video feed preview window inside ChatView:
  - Live 30 FPS camera preview
  - '📸 CAPTURE PHOTO' button
  - Saves snapshot image and attaches to InputPanel preview strip
"""

import time
import threading
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk
from .theme import C, F

class CameraModal:
    """ChatGPT-style camera popup overlay modal."""

    def __init__(self, parent: tk.Widget, on_capture: callable) -> None:
        self._parent = parent
        self._on_capture = on_capture
        self._cap = None
        self._running = False
        self._thread = None
        self._current_frame = None

        # Modal overlay background container
        self.overlay = tk.Frame(self._parent, bg=C.BG_OVERLAY if hasattr(C, 'BG_OVERLAY') else "#040612")
        self.overlay.place(relx=0.5, rely=0.45, anchor="center", relwidth=0.85, relheight=0.75)

        # Main glass window frame
        self.card = tk.Frame(
            self.overlay,
            bg=C.GLASS_4,
            highlightthickness=1,
            highlightbackground=C.GLASS_BD_4
        )
        self.card.pack(fill="both", expand=True, padx=2, pady=2)

        # Header bar
        hdr = tk.Frame(self.card, bg=C.GLASS_4, padx=12, pady=8)
        hdr.pack(fill="x")

        tk.Label(
            hdr, text="📷 CAMERA CAPTURE",
            font=(F._PRIMARY, F.MD, "bold"),
            bg=C.GLASS_4, fg=C.FG_1
        ).pack(side="left")

        close_btn = tk.Label(
            hdr, text="✕",
            font=(F._PRIMARY, F.MD, "bold"),
            bg=C.GLASS_4, fg=C.FG_3, cursor="hand2", padx=6
        )
        close_btn.pack(side="right")
        close_btn.bind("<ButtonRelease-1>", lambda e: self.close())

        # Live Video Preview Canvas
        self.preview_lbl = tk.Label(
            self.card, text="Initializing Camera Feed...",
            font=(F._FALLBACK, F.SM),
            bg="#000000", fg=C.FG_2
        )
        self.preview_lbl.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Bottom Control Bar: Capture Button
        ctrl = tk.Frame(self.card, bg=C.GLASS_4, padx=12, pady=10)
        ctrl.pack(fill="x")

        self.cap_btn = tk.Button(
            ctrl, text="📸 CAPTURE PHOTO",
            font=(F._PRIMARY, F.SM, "bold"),
            bg=C.BLUE, fg="#FFFFFF",
            activebackground=C.BLUE_L, activeforeground="#FFFFFF",
            relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
            command=self._do_capture
        )
        self.cap_btn.pack(anchor="center")

        # Start live video stream
        self._start_camera()

    def _start_camera(self) -> None:
        try:
            import cv2
            self._cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if self._cap.isOpened():
                self._running = True
                self._thread = threading.Thread(target=self._update_loop, daemon=True)
                self._thread.start()
            else:
                self.preview_lbl.configure(text="⚠ Camera device unavailable")
        except Exception as exc:
            self.preview_lbl.configure(text=f"⚠ Camera Error: {exc}")

    def _update_loop(self) -> None:
        import cv2
        while self._running and self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if ret and frame is not None:
                self._current_frame = frame.copy()
                # Convert BGR to RGB
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                img = img.resize((440, 280), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                try:
                    self.preview_lbl.configure(image=imgtk, text="")
                    self.preview_lbl.image = imgtk
                except Exception:
                    break
            time.sleep(0.03)

    def _do_capture(self) -> None:
        if self._current_frame is not None:
            try:
                import cv2
                temp_dir = Path(__file__).parent.parent / "scratch" / "camera"
                temp_dir.mkdir(parents=True, exist_ok=True)
                path = temp_dir / f"camera_photo_{int(time.time())}.png"
                cv2.imwrite(str(path), self._current_frame)
                if self._on_capture:
                    self._on_capture(str(path))
            except Exception as exc:
                print("Capture error:", exc)
        self.close()

    def close(self) -> None:
        self._running = False
        if self._cap and self._cap.isOpened():
            try:
                self._cap.release()
            except Exception:
                pass
        try:
            self.overlay.destroy()
        except Exception:
            pass
