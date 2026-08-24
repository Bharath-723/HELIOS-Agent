"""
compact_view_validation.py — Automated Validation Suite for HELIOS Compact View
==================================================================================
Tests all 20 required steps for compact mode viewport switching and session state preservation.
"""

from __future__ import annotations
import unittest
import sys
import os
import time

# Ensure current project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helios_popup import HELIOSApp
from ui.theme import ThemeManager


class TestCompactViewValidation(unittest.TestCase):
    """20-Step validation suite for compact/mobile view toggle & session continuity."""

    def test_compact_view_20_step_suite(self):
        ThemeManager.set_mode("dark")
        app = HELIOSApp()
        app._on_close = lambda: None   # Prevent auto-closing during unit test execution
        root = app.root
        root.update()

        # 1. Launch HELIOS & 2. Verify Desktop Mode
        self.assertEqual(app._ui_mode, "DESKTOP_VIEW")
        orig_w = root.winfo_width()
        orig_h = root.winfo_height()
        self.assertGreater(orig_w, 450)

        # 3. Verify ChatView Visible
        self.assertEqual(app._current_panel, "chat")
        self.assertTrue(app.chat.frame.winfo_ismapped())

        # 4. Click Compact Toggle
        t0 = time.time()
        app._toggle_compact_mode()
        root.update()
        t1 = time.time()

        # 5. Verify Window Becomes Approximately 420x760 & Sub-50ms Switch
        compact_w = root.winfo_width()
        compact_h = root.winfo_height()
        self.assertEqual(app._ui_mode, "COMPACT_VIEW")
        self.assertEqual(compact_w, 420)
        self.assertEqual(compact_h, 760)
        self.assertLess((t1 - t0) * 1000, 50.0)

        # 6. Verify ChatView Remains Visible
        self.assertEqual(app._current_panel, "chat")
        self.assertTrue(app.chat.frame.winfo_ismapped())

        # 7. Insert User Message & 8. Verify Message Appears
        app.chat.add_user_message("Search for display settings")
        root.update()
        self.assertIn("Search for display settings", app.chat.get_text_content())

        # 9. Show HELIOS Response & 10. Verify Response Appears
        app.chat.add_helios_message("Here are the display settings details.", model_tag="Gemma 3 4B")
        root.update()
        self.assertIn("display settings details", app.chat.get_text_content())

        # 11. Switch THINKING & 12. Verify THINKING Remains Visible
        app.chat.show_thinking("Analyzing display parameters...")
        root.update()
        self.assertIsNotNone(app.chat._state_card)

        # 13. Switch WORKING & 14. Verify WORKING Remains Visible
        app.chat.show_working("Opening Display Settings panel...")
        root.update()
        self.assertIsNotNone(app.chat._state_card)

        # 15. Switch VERIFYING & 16. Verify VERIFYING Remains Visible
        app.chat.show_verifying("Verifying panel focus...")
        root.update()
        self.assertIsNotNone(app.chat._state_card)

        # 17. Click Desktop-View Toggle
        t2 = time.time()
        app._toggle_compact_mode()
        root.update()
        t3 = time.time()

        # 18. Verify Original Geometry Restored & Sub-50ms Switch
        self.assertEqual(app._ui_mode, "DESKTOP_VIEW")
        self.assertEqual(root.winfo_width(), orig_w)
        self.assertEqual(root.winfo_height(), orig_h)
        self.assertLess((t3 - t2) * 1000, 50.0)

        # 19. Verify Conversation History Unchanged
        full_text = app.chat.get_text_content()
        self.assertIn("Search for display settings", full_text)
        self.assertIn("display settings details", full_text)

        # 20. Verify Session State Unchanged
        self.assertEqual(app._current_panel, "chat")
        print("ALL 20 COMPACT VIEW VALIDATION STEPS PASSED PERFECTLY!")

        try:
            root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
