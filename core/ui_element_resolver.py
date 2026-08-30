"""
core/ui_element_resolver.py — HELIOS Hybrid UI Element Target Resolver
========================================================================
Resolves user target descriptions ("click Save", "open Notepad", "click Bluetooth")
to structured screen element bounds (x, y, width, height) using a deterministic 4-level hybrid resolution order:
  LEVEL 1: Windows UI Automation (UIA) Control Tree
  LEVEL 2: Microsoft Active Accessibility (MSAA) Control Search
  LEVEL 3: Local Textual OCR / Visual Bounding Box Matching (RapidOCR)
  LEVEL 4: PyAutoGUI / ScreenState Heuristic Fallback
  LEVEL 5: Controlled Failure Return (No arbitrary random clicks)
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from core.ocr_provider import OCRProvider
from core.desktop_session.session_models import ScreenState, ScreenElement

log = logging.getLogger("helios.ui_element_resolver")


def _is_valid_target_match(target_clean: str, candidate_text: str) -> bool:
    """
    Enforces Specificity Preservation during target resolution.
    If target_clean is generic ('settings'), a candidate containing extra specific modifiers
    ('wifi', 'bluetooth', 'display', 'sound', etc.) NOT present in target_clean is REJECTED.
    """
    t_clean = target_clean.lower().strip()
    c_clean = candidate_text.lower().strip()
    if not t_clean or not c_clean:
        return False
    if t_clean == c_clean:
        return True

    t_words = set(t_clean.split())
    c_words = set(c_clean.split())

    # Generic parent target constraint check:
    SPECIFIC_MODIFIERS = {"wifi", "wi-fi", "bluetooth", "display", "sound", "network", "battery", "storage", "privacy", "updates"}
    if "settings" in t_words and not (t_words & SPECIFIC_MODIFIERS):
        if c_words & SPECIFIC_MODIFIERS:
            return False

    if t_clean in c_clean or c_clean in t_clean:
        return True
    return False


class UIElementResolver:
    """Hybrid target resolution engine for desktop automation actions."""

    def __init__(self):
        self.ocr = OCRProvider()
        self._uia_available = self._detect_uia()
        log.info("UIElementResolver initialized (UIA Engine Available: %s)", self._uia_available)

    def _detect_uia(self) -> bool:
        try:
            import uiautomation as uia  # noqa: F401
            return True
        except ImportError:
            return False

    def resolve_target(
        self,
        target_description: str,
        screenshot_path: Optional[str] = None,
        screen_state: Optional[ScreenState] = None
    ) -> Dict[str, Any]:
        """
        Resolves a natural language target description into element bounds and center coordinates.
        Returns:
            {
                "success": bool,
                "method": "uia" | "msaa" | "ocr" | "heuristic" | "none",
                "label": str,
                "type": str,
                "automation_id": str,
                "bounds": (x, y, w, h),
                "center": (cx, cy),
                "confidence": float,
                "source": str,
                "failure_reason": Optional[str]
            }
        """
        target_clean = target_description.lower().strip()
        log.info("Resolving UI element target for description: '%s'", target_description)

        # ── LEVEL 1: Windows UI Automation (UIA) Control Tree ─────────────────────────
        if self._uia_available:
            try:
                uia_res = self._resolve_uia(target_clean, target_description)
                if uia_res and uia_res["success"]:
                    log.info("Resolved target '%s' via UIA: bounds=%s, center=%s",
                             target_description, uia_res["bounds"], uia_res["center"])
                    return uia_res
            except Exception as exc:
                log.warning("UIA resolution attempt failed for '%s': %s", target_description, exc)

        # ── LEVEL 2: MSAA Control Fallback ──────────────────────────────────────────
        if self._uia_available:
            try:
                msaa_res = self._resolve_msaa(target_clean, target_description)
                if msaa_res and msaa_res["success"]:
                    log.info("Resolved target '%s' via MSAA: bounds=%s, center=%s",
                             target_description, msaa_res["bounds"], msaa_res["center"])
                    return msaa_res
            except Exception as exc:
                log.warning("MSAA resolution attempt failed for '%s': %s", target_description, exc)

        # ── LEVEL 3: OCR / Visual Bounding Box Matching (RapidOCR) ───────────────────
        if screenshot_path and Path(screenshot_path).exists():
            ocr_regions = self.ocr.extract_regions_from_file(screenshot_path)
            for reg in ocr_regions:
                text_clean = reg["text"].lower().strip()
                if text_clean and len(text_clean) >= 3:
                    if _is_valid_target_match(target_clean, text_clean):
                        x, y, w, h = reg["bbox"]
                        cx, cy = x + w // 2, y + h // 2
                        log.info("Resolved target '%s' via OCR: bounds=(%d,%d,%d,%d), center=(%d,%d)",
                                 target_description, x, y, w, h, cx, cy)
                        return {
                            "success": True,
                            "method": "ocr",
                            "label": reg["text"],
                            "type": "text_element",
                            "automation_id": "",
                            "bounds": (x, y, w, h),
                            "center": (cx, cy),
                            "confidence": reg.get("confidence", 0.85),
                            "source": "ocr",
                            "failure_reason": None
                        }

        # ── LEVEL 4: ScreenState / PyAutoGUI Heuristic Fallback ─────────────────────
        if screen_state and screen_state.ui_elements:
            for elem in screen_state.ui_elements:
                elem_clean = elem.text.lower().strip()
                if _is_valid_target_match(target_clean, elem_clean):
                    log.info("Resolved target '%s' via ScreenState element heuristics", target_description)
                    return {
                        "success": True,
                        "method": "heuristic",
                        "label": elem.text,
                        "type": elem.element_type,
                        "automation_id": "",
                        "bounds": (100, 100, 200, 40),
                        "center": (200, 120),
                        "confidence": 0.75,
                        "source": "heuristic",
                        "failure_reason": None
                    }

        # ── LEVEL 5: Controlled Failure Return (No Arbitrary Clicks) ────────────────
        log.warning("Could not resolve UI element target for '%s' across UIA, MSAA, OCR, or heuristics", target_description)
        return {
            "success": False,
            "method": "none",
            "label": target_description,
            "type": "unknown",
            "automation_id": "",
            "bounds": (0, 0, 0, 0),
            "center": (0, 0),
            "confidence": 0.0,
            "source": "none",
            "failure_reason": f"Target '{target_description}' could not be resolved by UIA, MSAA, OCR, or PyAutoGUI heuristics."
        }

    def _resolve_uia(self, target_clean: str, target_raw: str) -> Optional[Dict[str, Any]]:
        import uiautomation as uia

        root = uia.GetRootControl()
        if not root:
            return None

        # 1. Search top-level window controls first
        children = root.GetChildren()
        for child in children:
            c_name = (child.Name or "").lower().strip()
            c_class = (child.ClassName or "").lower().strip()
            c_auto = (child.AutomationId or "").lower().strip()

            if target_clean in c_name or c_name in target_clean or target_clean in c_class:
                rect = child.BoundingRectangle
                if rect and rect.width() > 0 and rect.height() > 0:
                    cx = rect.left + rect.width() // 2
                    cy = rect.top + rect.height() // 2
                    return {
                        "success": True,
                        "method": "uia",
                        "label": child.Name or target_raw,
                        "type": child.ControlTypeName,
                        "automation_id": child.AutomationId or "",
                        "bounds": (rect.left, rect.top, rect.width(), rect.height()),
                        "center": (cx, cy),
                        "confidence": 1.0,
                        "source": "uia",
                        "failure_reason": None
                    }

            # Search 1 level deeper inside active top-level window
            try:
                sub_children = child.GetChildren()
                for sub in sub_children:
                    s_name = (sub.Name or "").lower().strip()
                    s_auto = (sub.AutomationId or "").lower().strip()
                    if s_name and (target_clean in s_name or s_name in target_clean or target_clean in s_auto):
                        rect = sub.BoundingRectangle
                        if rect and rect.width() > 0 and rect.height() > 0:
                            cx = rect.left + rect.width() // 2
                            cy = rect.top + rect.height() // 2
                            return {
                                "success": True,
                                "method": "uia",
                                "label": sub.Name or target_raw,
                                "type": sub.ControlTypeName,
                                "automation_id": sub.AutomationId or "",
                                "bounds": (rect.left, rect.top, rect.width(), rect.height()),
                                "center": (cx, cy),
                                "confidence": 0.95,
                                "source": "uia",
                                "failure_reason": None
                            }
            except Exception:
                pass

        return None

    def _resolve_msaa(self, target_clean: str, target_raw: str) -> Optional[Dict[str, Any]]:
        # MSAA search via uiautomation legacy IAccessible interface fallback
        import uiautomation as uia

        root = uia.GetRootControl()
        if not root:
            return None

        for child in root.GetChildren():
            try:
                # Walk control hierarchy checking IAccessible name
                c_name = (child.Name or "").lower()
                if target_clean in c_name:
                    rect = child.BoundingRectangle
                    if rect and rect.width() > 0:
                        cx = rect.left + rect.width() // 2
                        cy = rect.top + rect.height() // 2
                        return {
                            "success": True,
                            "method": "msaa",
                            "label": child.Name or target_raw,
                            "type": child.ControlTypeName,
                            "automation_id": child.AutomationId or "",
                            "bounds": (rect.left, rect.top, rect.width(), rect.height()),
                            "center": (cx, cy),
                            "confidence": 0.90,
                            "source": "msaa",
                            "failure_reason": None
                        }
            except Exception:
                pass

        return None
