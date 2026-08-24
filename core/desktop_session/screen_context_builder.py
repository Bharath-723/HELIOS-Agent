"""
core/desktop_session/screen_context_builder.py — Screen Context Builder
========================================================================
Converts full ScreenState objects into minimized, structured context payloads
optimized for LLM prompt construction without unneeded overhead.
"""

import logging
from typing import Dict, Any, Optional
from .session_models import ScreenState

log = logging.getLogger("helios.desktop_session.context_builder")


class ScreenContextBuilder:
    """Builds minimized screen context representations."""

    @classmethod
    def build_minimal_context(
        cls,
        screen_state: ScreenState,
        task_instruction: str = "",
        include_full_screenshot: bool = False
    ) -> Dict[str, Any]:
        """
        Build minimal screen context payload following strict priority:
        1. Active application / window metadata
        2. UI elements summary
        3. OCR / text summary
        4. Relevant screen region / bounds
        5. Full screenshot path only if explicitly requested
        """
        if not screen_state:
            return {
                "active_window_title": "Desktop",
                "active_app_name": "explorer.exe",
                "screen_summary": "Desktop visible",
            }

        elements_summary = [
            f"[{e.element_type}] {e.text}"
            for e in screen_state.ui_elements[:10]
            if e.text
        ]

        payload: Dict[str, Any] = {
            "active_window_title": screen_state.active_window_title,
            "active_app_name": screen_state.active_app_name,
            "visible_elements": elements_summary,
            "ocr_summary": screen_state.ocr_text[:500] if screen_state.ocr_text else "",
            "screen_summary": screen_state.screen_summary,
        }

        if include_full_screenshot and screen_state.screenshot_path:
            payload["screenshot_path"] = screen_state.screenshot_path

        log.debug("ScreenContextBuilder: Built minimal context payload (%d bytes)", len(str(payload)))
        return payload
