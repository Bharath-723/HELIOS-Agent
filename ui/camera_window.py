"""
ui/camera_window.py — HELIOS In-App Camera Capture Modal
======================================================
Provides live webcam preview window inside HELIOS.
Captures photos and attaches them directly to the chat box.
"""

from __future__ import annotations
import sys
import logging
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from ui.theme import C, F

log = logging.getLogger("helios.ui.camera")

try:
    import cv2
    from PIL import Image, ImageTk
    _CAMERA_LIBS_AVAILABLE = True
except ImportError:
    _CAMERA_LIBS_AVAILABLE = False


class CameraCaptureWindow:
    def __init__(self, parent_root: tk.Tk, on_capture: callable) -> None:
        self.parent = parent_root
        self.on_capture = on_capture
        self.cap = None
        self.running = False
        self._photo_ref = None

        self.win = tk.Toplevel(parent_root)
        self.win.title("HELIOS Camera")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=C.BG)

        # Center window over parent
        pw = parent_root.winfo_width()
        ph = parent_root.winfo_height()
        px = parent_root.winfo_x()
        py = parent_root.winfo_y()

        w, h = 480, 420
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        # Main border frame
        self.border_frame = tk.Frame(self.win, bg=C.BORDER, padx=1, pady=1)
        self.border_frame.pack(fill="both", expand=True)

        self.container = tk.Frame(self.border_frame, bg=C.BG)
        self.container.pack(fill="both", expand=True)

        # Header bar
        hdr = tk.Frame(self.container, bg=C.BG, padx=12, pady=8)
        hdr.pack(fill="x")

        tk.Label(hdr, text="📷 HELIOS Camera", font=(F._PRIMARY, F.MD, "bold"), bg=C.BG, fg=C.FG_1).pack(side="left")
        self.lbl_live = tk.Label(hdr, text="  ● LIVE  ", font=(F._FALLBACK, F.XS, "bold"), bg=C.OK_D, fg=C.OK_L, padx=4, pady=1)
        self.lbl_live.pack(side="left", padx=8)

        btn_close = tk.Label(hdr, text="✕", font=(F._FALLBACK, F.MD), bg=C.BG, fg=C.FG_3, cursor="hand2")
        btn_close.pack(side="right")
        btn_close.bind("<ButtonRelease-1>", lambda e: self.close())

        # Video Canvas
        self.canvas = tk.Canvas(self.container, bg="#0F172A", highlightthickness=0, width=456, height=310)
        self.canvas.pack(padx=12, pady=4)

        # Control Bar
        ctrl = tk.Frame(self.container, bg=C.BG, padx=12, pady=10)
        ctrl.pack(fill="x")

        self.btn_snap = tk.Button(
            ctrl,
            text="📸 CAPTURE & ATTACH",
            font=(F._PRIMARY, F.SM, "bold"),
            bg=C.BLUE, fg="white",
            activebackground=C.BLUE_L, activeforeground="white",
            relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
            command=self._take_snapshot
        )
        self.btn_snap.pack(side="left", expand=True)

        btn_gallery = tk.Button(
            ctrl,
            text="🖼 GALLERY",
            font=(F._FALLBACK, F.SM),
            bg=C.BG_C2, fg=C.FG_1,
            activebackground=C.BG_S, activeforeground=C.FG_1,
            relief="flat", bd=0, padx=10, pady=6, cursor="hand2",
            command=self._pick_file
        )
        btn_gallery.pack(side="left", padx=6)

        self._start_camera()

    def _start_camera(self) -> None:
        if not _CAMERA_LIBS_AVAILABLE:
            self._show_error("OpenCV or Pillow missing.")
            return

        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if sys.platform.startswith("win") else 0)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)

            if self.cap.isOpened():
                self.running = True
                self._tick()
            else:
                self._show_error("No webcam detected.")
        except Exception as ex:
            self._show_error(f"Camera error: {ex}")

    def _tick(self) -> None:
        if not self.running or not self.cap or not self.win.winfo_exists():
            return
        ret, frame = self.cap.read()
        if ret and frame is not None:
            self._current_frame = frame.copy()
            # Convert BGR to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img = img.resize((456, 310), Image.Resampling.LANCZOS)
            self._photo_ref = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, image=self._photo_ref, anchor="nw")
        
        self.win.after(30, self._tick)

    def _show_error(self, msg: str) -> None:
        self.lbl_live.configure(text="  OFFLINE  ", bg=C.ERR_CARD_BG, fg=C.ERR_L)
        self.canvas.create_text(228, 155, text=f"📷 {msg}\nClick GALLERY to pick a photo.", font=(F._FALLBACK, F.SM), fill=C.FG_3, justify="center")

    def _take_snapshot(self) -> None:
        if hasattr(self, "_current_frame") and self._current_frame is not None:
            try:
                from core.system import paths_manager
                from datetime import datetime
                img_dir = paths_manager.files_dir
                img_dir.mkdir(parents=True, exist_ok=True)
                fname = f"camera_snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                fpath = str(img_dir / fname)
                cv2.imwrite(fpath, self._current_frame)
                
                self.on_capture(fpath)
                self.close()
                return
            except Exception as exc:
                log.error("Failed to save camera snapshot: %s", exc)

        # Fallback if no frame active
        self._pick_file()

    def _pick_file(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.win,
            title="Select Image File",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.bmp")]
        )
        if path:
            self.on_capture(path)
            self.close()

    def close(self) -> None:
        self.running = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        if self.win.winfo_exists():
            self.win.destroy()
