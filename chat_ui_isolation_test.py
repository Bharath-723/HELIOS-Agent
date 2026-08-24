"""
chat_ui_isolation_test.py — Phase 13 HELIOS Chat UI Isolation Test
====================================================================
Starts ONLY the HELIOS Chat UI, renders test messages, 20 sequential messages,
verifies scrolling, and adds a delayed message after 2s.
"""

import sys
import time
import tkinter as tk

sys.path.insert(0, ".")

from ui.theme import ThemeManager, C, W
from ui.chat_view import ChatView


def run_chat_ui_isolation():
    print("=" * 60)
    print("STARTING PHASE 13 CHAT UI ISOLATION TEST")
    print("=" * 60)

    root = tk.Tk()
    root.title("HELIOS Chat UI Isolation Test")
    root.geometry(f"{W.WIDTH}x{W.HEIGHT}")
    root.configure(bg=C.BG)

    ThemeManager.set_mode("dark")

    panel_area = tk.Frame(root, bg=C.BG_S)
    panel_area.pack(fill="both", expand=True)

    chat = ChatView(panel_area)
    chat.frame.pack(fill="both", expand=True)

    root.update()

    # 1. Direct Static Notice
    chat.add_system_notice("HELIOS CHAT UI TEST — VISIBLE")

    # 2. Render User Message
    chat.add_user_message("Hello HELIOS! This is a test user message.")

    # 3. Render HELIOS Assistant Message
    card, txt, lbl = chat.add_streaming_helios_message()
    chat.update_streaming_content(txt, lbl, "Hello User! This is a static assistant response from HELIOS.")

    # 4. Render Multiline Message
    multiline = "Line 1: HELIOS Persistent Screen-Aware Desktop Agent.\n" * 5
    card2, txt2, lbl2 = chat.add_streaming_helios_message()
    chat.update_streaming_content(txt2, lbl2, multiline)

    # 5. Render 20 Sequential Messages
    for i in range(1, 21):
        chat.add_user_message(f"User instruction #{i}")
        c, t, l = chat.add_streaming_helios_message()
        chat.update_streaming_content(t, l, f"HELIOS response #{i} for user instruction.")

    root.update()

    # 6. Verify Scrolling
    chat._scroll_to_bottom(force=True)
    root.update()

    print(f"\n[ISOLATION DIAGNOSTIC]")
    print(f"history_count=43")
    print(f"message_widget_count={len(chat.msgs.winfo_children())}")
    print(f"canvas_width={chat.canvas.winfo_width()}")
    print(f"canvas_height={chat.canvas.winfo_height()}")
    print(f"msgs_width={chat.msgs.winfo_width()}")
    print(f"msgs_req_height={chat.msgs.winfo_reqheight()}")
    print(f"scrollregion={chat.canvas.cget('scrollregion')}")

    # 7. Add another message after 2 seconds
    def _delayed_msg():
        chat.add_user_message("Delayed message after 2 seconds")
        c3, t3, l3 = chat.add_streaming_helios_message()
        chat.update_streaming_content(t3, l3, "HELIOS received delayed instruction after 2s.")
        root.update()
        print("\nDelayed 2s message successfully added.")
        root.destroy()

    root.after(2000, _delayed_msg)
    root.mainloop()

    print("=" * 60)
    print("PHASE 13 CHAT UI ISOLATION TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run_chat_ui_isolation()
