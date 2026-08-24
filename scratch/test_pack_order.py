import sys
import tkinter as tk

sys.path.insert(0, ".")
from ui.theme import ThemeManager, C, W

root = tk.Tk()
root.geometry("460x740")
ThemeManager.set_mode("dark")

main = tk.Frame(root, bg=C.BG)
main.pack(fill="both", expand=True)

# 1. Header (top)
header = tk.Frame(main, bg="red", height=60)
header.pack(side="top", fill="x")

# 2. Status bar (bottom-most)
status = tk.Frame(main, bg="green", height=26)
status.pack(side="bottom", fill="x")

# 3. Input panel (bottom above status bar)
inp = tk.Frame(main, bg="yellow", height=84)
inp.pack(side="bottom", fill="x")

# 4. Content area (fills exact remaining space in center)
content = tk.Frame(main, bg="blue")
content.pack(side="top", fill="both", expand=True)

root.update()

print("Main size:", main.winfo_width(), "x", main.winfo_height())
print("Header size:", header.winfo_width(), "x", header.winfo_height(), "y:", header.winfo_y())
print("Status size:", status.winfo_width(), "x", status.winfo_height(), "y:", status.winfo_y())
print("Input size:", inp.winfo_width(), "x", inp.winfo_height(), "y:", inp.winfo_y())
print("Content size:", content.winfo_width(), "x", content.winfo_height(), "y:", content.winfo_y())

root.destroy()
