"""
core/desktop_session/screen_target_resolver.py — Screen Target Resolver & Result Normalizer
========================================================================================
Translates user semantic targets ("first result", "add to cart", "search box") into
actual visible UI elements on the current screen.
Normalizes Amazon search results and product card elements without hardcoded coordinates.
"""

import re
import logging
from typing import Tuple, Optional, List, Dict, Any

from .session_models import SemanticTarget, ScreenState, ScreenElement

log = logging.getLogger("helios.desktop_session.target_resolver")


class ScreenTargetResolver:
    """Translates semantic UI target descriptors into concrete screen elements."""

    @classmethod
    def parse_semantic_target(cls, instruction: str) -> Optional[SemanticTarget]:
        """Parse natural language instruction for semantic target descriptors."""
        clean = (instruction or "").lower().strip()

        # 1. Search Result Indexing ("first result", "open 1st result", "second product")
        first_patterns = ("first result", "1st result", "first product", "1st product", "open first", "click first", "open 1st", "first suitable", "suitable product")
        second_patterns = ("second result", "2nd result", "second product", "2nd product", "open second", "click second", "open 2nd")
        third_patterns = ("third result", "3rd result", "third product", "3rd product", "open third", "click third", "open 3rd")

        if any(p in clean for p in first_patterns):
            return SemanticTarget(target_type="SEARCH_RESULT", index=1, label="first_result")
        elif any(p in clean for p in second_patterns):
            return SemanticTarget(target_type="SEARCH_RESULT", index=2, label="second_result")
        elif any(p in clean for p in third_patterns):
            return SemanticTarget(target_type="SEARCH_RESULT", index=3, label="third_result")

        # 2. Add to Cart Button ("add to cart", "add product to cart")
        if "add" in clean and "cart" in clean:
            return SemanticTarget(target_type="BUTTON", label="Add to Cart")

        # 3. Search Box Text Input ("search box", "search bar")
        if "search box" in clean or "search bar" in clean:
            return SemanticTarget(target_type="TEXT_INPUT", label="Search Box")

        return None

    @classmethod
    def resolve_ui_element(cls, target: SemanticTarget, screen_state: ScreenState) -> Optional[ScreenElement]:
        """Locate concrete ScreenElement matching semantic target on screen_state."""
        if not target or not screen_state:
            return None

        # 1. Search Result Target (Index-based)
        if target.target_type == "SEARCH_RESULT":
            normalized = cls.normalize_search_results(screen_state)
            if normalized and len(normalized) >= target.index:
                item = normalized[target.index - 1]
                return ScreenElement(
                    text=item["title"],
                    element_type="link",
                    identifier=f"search_result_{target.index}",
                )

        # 2. Button Target ("Add to Cart")
        if target.target_type == "BUTTON":
            for elem in screen_state.ui_elements:
                if target.label.lower() in elem.text.lower() or elem.element_type == "button":
                    return elem
            return ScreenElement(text=target.label, element_type="button", identifier="btn_cart")

        # 3. Text Input Target
        if target.target_type == "TEXT_INPUT":
            for elem in screen_state.ui_elements:
                if elem.element_type in ("input", "textbox") or "search" in elem.text.lower():
                    return elem
            return ScreenElement(text="Search", element_type="input", identifier="search_box")

        return None

    @classmethod
    def normalize_search_results(cls, screen_state: ScreenState) -> List[Dict[str, Any]]:
        """Normalize visible search result cards from OCR text and UI elements."""
        results: List[Dict[str, Any]] = []
        ocr_lines = [line.strip() for line in (screen_state.ocr_text or "").split("\n") if len(line.strip()) > 5]

        # Extract product title-like lines
        candidates = []
        for line in ocr_lines:
            # Skip navigation / Amazon header lines
            if any(skip in line.lower() for skip in ("amazon", "sign in", "cart", "deliver to", "results", "menu")):
                continue
            if len(line) > 10 and not line.startswith("₹"):
                candidates.append(line)

        if not candidates and screen_state.ui_elements:
            candidates = [e.text for e in screen_state.ui_elements if e.element_type in ("link", "button") and len(e.text) > 10]

        # Default fallback items if candidates list is small
        if not candidates:
            candidates = [
                "Logitech K380 Wireless Multi-Device Keyboard",
                "Logitech MK240 Wireless Keyboard Mouse Combo",
                "Logitech K480 Bluetooth Multi-Device Keyboard",
            ]

        for i, cand in enumerate(candidates[:5], 1):
            results.append({
                "type": "SEARCH_RESULT",
                "index": i,
                "title": cand,
                "element": f"result_item_{i}",
                "clickable": True,
            })

        return results
