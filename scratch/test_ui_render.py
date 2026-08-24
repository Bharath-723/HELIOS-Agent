import tkinter as tk
import logging
import sys

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("ui_test")

try:
    sys.path.insert(0, ".")
    from ui.theme import ThemeManager, C
    from ui.chat_view import ChatView
    from ui.home_screen import HomeScreen

    root = tk.Tk()
    root.geometry("460x740")
    ThemeManager.set_mode("dark")

    panel_area = tk.Frame(root, bg=C.BG_S)
    panel_area.pack(fill="both", expand=True)

    chat = ChatView(panel_area)
    chat.frame.pack(fill="both", expand=True)

    root.update_idletasks()
    log.info("ChatView instantiated successfully. Children count in msgs: %d", len(chat.msgs.winfo_children()))
    if chat._home_view:
        log.info("HomeScreen frame children count: %d", len(chat._home_view.frame.winfo_children()))
        log.info("HomeScreen container children count: %d", len(chat._home_view.container.winfo_children()))

    root.destroy()
    print("SUCCESS: ChatView & HomeScreen rendered without errors.")
except Exception as ex:
    import traceback
    print("ERROR rendering ChatView/HomeScreen:", ex)
    traceback.print_exc()
