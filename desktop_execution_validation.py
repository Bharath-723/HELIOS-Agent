"""
desktop_execution_validation.py — HELIOS Target Resolution & Execution Validation Suite
========================================================================================
Validates:
1. test_open_chrome_resolves_chrome_exe
2. test_open_url_is_not_treated_as_file
3. test_unknown_application_does_not_create_url_shortcut
4. test_missing_executable_fails_cleanly
5. test_no_arbitrary_url_shortcut_generation
6. test_gprolog_url_regression
"""

import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.desktop_session import (
    TargetResolver,
    TargetCategory,
    DesktopSessionManager,
    DesktopSessionState,
)
from modules.desktop_agent import DesktopAgent


class DesktopExecutionValidationSuite(unittest.TestCase):

    def setUp(self):
        self.desktop = DesktopAgent()

    # 1. Open Chrome resolves chrome.exe
    def test_open_chrome_resolves_chrome_exe(self):
        cat, resolved, details = TargetResolver.resolve_target("Chrome")
        self.assertEqual(cat, TargetCategory.APPLICATION)
        self.assertIn("chrome", resolved.lower())

    # 2. Open URL is not treated as file
    def test_open_url_is_not_treated_as_file(self):
        cat1, res1, _ = TargetResolver.resolve_target("https://www.amazon.in")
        cat2, res2, _ = TargetResolver.resolve_target("amazon.in")
        self.assertEqual(cat1, TargetCategory.URL)
        self.assertEqual(cat2, TargetCategory.URL)
        self.assertTrue(res1.startswith("https://"))
        self.assertTrue(res2.startswith("https://"))

    # 3. Unknown application does not create .url shortcut
    def test_unknown_application_does_not_create_url_shortcut(self):
        cat, resolved, details = TargetResolver.resolve_target("some_fake_app_xyz_123")
        self.assertEqual(cat, TargetCategory.UNKNOWN)
        self.assertIsNone(resolved)
        self.assertNotIn(".url", details)

    # 4. Missing executable fails cleanly
    def test_missing_executable_fails_cleanly(self):
        msg = self.desktop.open_app("non_existent_app_xyz_999")
        self.assertIn("Could not find or launch", msg)
        self.assertIn("non_existent_app_xyz_999", msg)

    # 5. No arbitrary url shortcut generation
    def test_no_arbitrary_url_shortcut_generation(self):
        cat, resolved, details = TargetResolver.resolve_target("mycustomapp")
        self.assertNotEqual(resolved, "mycustomapp.url")
        self.assertEqual(cat, TargetCategory.UNKNOWN)

    # 6. gprolog.url regression test
    def test_gprolog_url_regression(self):
        cat1, res1, details1 = TargetResolver.resolve_target("gprolog")
        cat2, res2, details2 = TargetResolver.resolve_target("gprolog.url")
        self.assertEqual(cat1, TargetCategory.UNKNOWN)
        self.assertEqual(cat2, TargetCategory.UNKNOWN)
        self.assertIsNone(res1)
        self.assertIsNone(res2)

        # Test desktop.open_app cleanly returns error without Windows dialog
        msg = self.desktop.open_app("gprolog")
        self.assertIn("Could not find or launch 'gprolog'", msg)


if __name__ == "__main__":
    unittest.main()
