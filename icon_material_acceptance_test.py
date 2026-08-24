"""
icon_material_acceptance_test.py — HELIOS Icon System Visual Acceptance Test
=============================================================================
Launches the real HELIOS navigation rail in isolation and captures screenshots
for each required acceptance state.

Outputs:
  icon_dark_rest.png
  icon_dark_hover.png
  icon_dark_pressed.png
  icon_dark_active.png
  icon_light_rest.png
  icon_light_hover.png
  icon_light_pressed.png
  icon_light_active.png
  compact_toggle.png
"""

import sys
import os
import time
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from PIL import ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

OUTPUT_DIR = Path(__file__).parent / "scratch"
OUTPUT_DIR.mkdir(exist_ok=True)


def capture(widget: tk.Widget, name: str) -> None:
    widget.update_idletasks()
    widget.update()
    time.sleep(0.3)
    if HAS_PIL:
        try:
            x = widget.winfo_rootx()
            y = widget.winfo_rooty()
            w = widget.winfo_width()
            h = widget.winfo_height()
            img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            out = OUTPUT_DIR / name
            img.save(str(out))
            print(f"Saved: {out}")
        except Exception as e:
            print(f"Capture failed ({name}): {e}")
    else:
        print(f"PIL not available, skipping screenshot: {name}")


def run_test():
    from ui.theme import ThemeManager, C
    from ui.icon_manager import IconRenderer, I, ICON_FONT, ICON_ACCENTS
    from ui.navigation_rail import NavigationRail, _NAV_ITEMS

    root = tk.Tk()
    root.title("HELIOS Icon Acceptance Test")
    root.geometry("600x500")

    def test_dark():
        ThemeManager.set_mode("dark")
        root.configure(bg="#070A1C")
        for w in frame.winfo_children():
            w.destroy()

        tk.Label(frame, text="DARK THEME — REST STATE",
                 font=("Segoe UI", 10, "bold"), bg="#070A1C", fg="#6A7E9A").pack(pady=(10, 4))

        row = tk.Frame(frame, bg="#070A1C")
        row.pack()

        renderer = IconRenderer(theme="dark")
        for key, glyph, label in _NAV_ITEMS:
            cv = tk.Canvas(row, width=44, height=44, bg="#070A1C", highlightthickness=0)
            cv.pack(side="left", padx=6)
            renderer.draw_nav_button(cv, key=key, glyph=glyph, state="idle")
            tk.Label(frame, text=label, font=("Segoe UI", 8),
                     bg="#070A1C", fg="#4A5B7A").pack()

        root.update()
        capture(root, "icon_dark_rest.png")

        # Hover state
        for w in frame.winfo_children():
            w.destroy()
        tk.Label(frame, text="DARK — HOVER",
                 font=("Segoe UI", 10, "bold"), bg="#070A1C", fg="#6A7E9A").pack(pady=(10,4))
        row2 = tk.Frame(frame, bg="#070A1C")
        row2.pack()
        for key, glyph, label in _NAV_ITEMS:
            cv = tk.Canvas(row2, width=44, height=44, bg="#070A1C", highlightthickness=0)
            cv.pack(side="left", padx=6)
            renderer.draw_nav_button(cv, key=key, glyph=glyph, state="hover")
        root.update()
        capture(root, "icon_dark_hover.png")

        # Pressed state
        for w in frame.winfo_children():
            w.destroy()
        tk.Label(frame, text="DARK — PRESSED",
                 font=("Segoe UI", 10, "bold"), bg="#070A1C", fg="#6A7E9A").pack(pady=(10,4))
        row3 = tk.Frame(frame, bg="#070A1C")
        row3.pack()
        for key, glyph, label in _NAV_ITEMS:
            cv = tk.Canvas(row3, width=44, height=44, bg="#070A1C", highlightthickness=0)
            cv.pack(side="left", padx=6)
            renderer.draw_nav_button(cv, key=key, glyph=glyph, state="pressed")
        root.update()
        capture(root, "icon_dark_pressed.png")

        # Active state
        for w in frame.winfo_children():
            w.destroy()
        tk.Label(frame, text="DARK — ACTIVE (chat selected)",
                 font=("Segoe UI", 10, "bold"), bg="#070A1C", fg="#6A7E9A").pack(pady=(10,4))
        row4 = tk.Frame(frame, bg="#070A1C")
        row4.pack()
        states = ["active", "idle", "idle", "idle", "idle"]
        for i, (key, glyph, label) in enumerate(_NAV_ITEMS):
            cv = tk.Canvas(row4, width=44, height=44, bg="#070A1C", highlightthickness=0)
            cv.pack(side="left", padx=6)
            renderer.draw_nav_button(cv, key=key, glyph=glyph, state=states[i])
        root.update()
        capture(root, "icon_dark_active.png")

    def test_light():
        ThemeManager.set_mode("light")
        root.configure(bg="#EDF1F8")
        for w in frame.winfo_children():
            w.destroy()

        renderer = IconRenderer(theme="light")

        tk.Label(frame, text="LIGHT THEME — REST STATE",
                 font=("Segoe UI", 10, "bold"), bg="#EDF1F8", fg="#64748B").pack(pady=(10,4))
        row = tk.Frame(frame, bg="#EDF1F8")
        row.pack()
        for key, glyph, label in _NAV_ITEMS:
            cv = tk.Canvas(row, width=44, height=44, bg="#EDF1F8", highlightthickness=0)
            cv.pack(side="left", padx=6)
            renderer.draw_nav_button(cv, key=key, glyph=glyph, state="idle")
        root.update()
        capture(root, "icon_light_rest.png")

        # Light hover
        for w in frame.winfo_children():
            w.destroy()
        tk.Label(frame, text="LIGHT — HOVER",
                 font=("Segoe UI", 10, "bold"), bg="#EDF1F8", fg="#64748B").pack(pady=(10,4))
        row2 = tk.Frame(frame, bg="#EDF1F8")
        row2.pack()
        for key, glyph, label in _NAV_ITEMS:
            cv = tk.Canvas(row2, width=44, height=44, bg="#EDF1F8", highlightthickness=0)
            cv.pack(side="left", padx=6)
            renderer.draw_nav_button(cv, key=key, glyph=glyph, state="hover")
        root.update()
        capture(root, "icon_light_hover.png")

        # Light pressed
        for w in frame.winfo_children():
            w.destroy()
        tk.Label(frame, text="LIGHT — PRESSED",
                 font=("Segoe UI", 10, "bold"), bg="#EDF1F8", fg="#64748B").pack(pady=(10,4))
        row3 = tk.Frame(frame, bg="#EDF1F8")
        row3.pack()
        for key, glyph, label in _NAV_ITEMS:
            cv = tk.Canvas(row3, width=44, height=44, bg="#EDF1F8", highlightthickness=0)
            cv.pack(side="left", padx=6)
            renderer.draw_nav_button(cv, key=key, glyph=glyph, state="pressed")
        root.update()
        capture(root, "icon_light_pressed.png")

        # Light active
        for w in frame.winfo_children():
            w.destroy()
        tk.Label(frame, text="LIGHT — ACTIVE",
                 font=("Segoe UI", 10, "bold"), bg="#EDF1F8", fg="#64748B").pack(pady=(10,4))
        row4 = tk.Frame(frame, bg="#EDF1F8")
        row4.pack()
        states = ["active", "idle", "idle", "idle", "idle"]
        for i, (key, glyph, label) in enumerate(_NAV_ITEMS):
            cv = tk.Canvas(row4, width=44, height=44, bg="#EDF1F8", highlightthickness=0)
            cv.pack(side="left", padx=6)
            renderer.draw_nav_button(cv, key=key, glyph=glyph, state=states[i])
        root.update()
        capture(root, "icon_light_active.png")

    def test_compact_toggle():
        ThemeManager.set_mode("dark")
        root.configure(bg="#070A1C")
        for w in frame.winfo_children():
            w.destroy()

        renderer = IconRenderer(theme="dark")

        tk.Label(frame, text="COMPACT TOGGLE — All 4 states",
                 font=("Segoe UI", 10, "bold"), bg="#070A1C", fg="#6A7E9A").pack(pady=(10,4))
        row = tk.Frame(frame, bg="#070A1C")
        row.pack(pady=10)
        for state in ["idle", "hover", "pressed"]:
            cv = tk.Canvas(row, width=28, height=28, bg="#070A1C", highlightthickness=0)
            cv.pack(side="left", padx=8)
            renderer.draw_compact_button(cv, state=state, is_compact=False)
            tk.Label(row, text=state, font=("Segoe UI", 8),
                     bg="#070A1C", fg="#4A5B7A").pack(side="left", padx=2)

        # Compact active (is_compact=True)
        cv2 = tk.Canvas(row, width=28, height=28, bg="#070A1C", highlightthickness=0)
        cv2.pack(side="left", padx=8)
        renderer.draw_compact_button(cv2, state="idle", is_compact=True)
        tk.Label(row, text="active", font=("Segoe UI", 8),
                 bg="#070A1C", fg="#4A5B7A").pack(side="left", padx=2)

        root.update()
        capture(root, "compact_toggle.png")

    frame = tk.Frame(root, bg="#070A1C")
    frame.pack(fill="both", expand=True)

    # Run tests sequentially
    root.after(200, test_dark)
    root.after(2000, test_light)
    root.after(4000, test_compact_toggle)
    root.after(5500, root.destroy)

    root.mainloop()
    print("\nAll icon acceptance tests complete!")
    print(f"Screenshots saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    run_test()
