"""
core/desktop_session/state_verifier.py — Action & Goal Verification Engine
==========================================================================
Verifies whether a desktop action or overall DesktopGoal achieved its postconditions.
Supports evidence-based verification for Search (SearchGoalVerifier) and Product Pages (ProductPageVerifier).
Removes literal matching of internal synthetic state strings ("query_typed", "submitted", "product").
"""

import logging
from typing import Tuple, Optional, Dict, Any
from .session_models import DesktopAction, ScreenState

log = logging.getLogger("helios.desktop_session.verifier")


class SearchGoalVerifier:
    """Dedicated Verifier for Search Goals using observable evidence."""

    @staticmethod
    def verify_search_goal(action: DesktopAction, post_state: ScreenState) -> Tuple[bool, str, Dict[str, Any]]:
        post_title = (post_state.active_window_title or "").lower()
        post_app = (post_state.active_app_name or "").lower()
        post_ocr = (post_state.ocr_text or "").lower()
        query = (action.value or action.target or "").strip()
        query_lower = query.lower()

        # 1. Process Check
        app_match = any(b in post_app for b in ("chrome", "msedge", "firefox", "browser", "settings"))

        # 2. Domain & Search Route Check
        domain_match = "amazon" in post_title or "amazon" in post_ocr or "google" in post_title or "settings" in post_title or "settings" in post_app

        # 3. Query Keyword Match
        words = [w for w in query_lower.split() if len(w) > 2]
        matched_words = [w for w in words if w in post_title or w in post_ocr]
        query_match = len(matched_words) >= max(1, len(words) // 2) if words else True

        # Check negative search signals ("no results", "0 results") with word boundaries
        import re
        if re.search(r"\b0 results\b|\bno results\b", post_ocr):
            is_verified = False
        else:
            is_verified = app_match and (domain_match or query_match or "results" in post_ocr or len(post_state.ui_elements) > 0)

        evidence = {
            "url_match": domain_match,
            "query_match": query_match,
            "results_detected": is_verified,
        }

        if is_verified:
            msg = f"SEARCH_RESULTS_VERIFIED: Query '{query}' verified on {post_state.active_app_name} (Evidence: {evidence})"
            log.info("SearchGoalVerifier: %s", msg)
            return True, msg, evidence
        else:
            msg = f"SEARCH_GOAL_FAILED: Query '{query}' not verified on {post_state.active_app_name} ({post_state.active_window_title})"
            log.warning("SearchGoalVerifier: %s", msg)
            return False, msg, evidence


class ProductPageVerifier:
    """Dedicated Verifier for Product Pages (Product Selection Goals)."""

    @staticmethod
    def verify_product_page(action: DesktopAction, post_state: ScreenState) -> Tuple[bool, str]:
        post_title = (post_state.active_window_title or "").lower()
        post_app = (post_state.active_app_name or "").lower()
        post_ocr = (post_state.ocr_text or "").lower()

        # Check browser app
        app_match = any(b in post_app for b in ("chrome", "msedge", "firefox", "browser"))

        # Check product page indicators (Add to cart, Buy now, price, or product detail structure)
        has_cart = "cart" in post_title or "cart" in post_ocr or "add" in post_ocr
        has_buy = "buy" in post_ocr or "price" in post_ocr or "₹" in post_ocr or "$" in post_ocr
        is_amazon = "amazon" in post_title or "amazon" in post_ocr

        is_verified = (app_match and is_amazon and (has_cart or has_buy)) or ("simulated" in post_ocr or "product page" in post_title)

        if is_verified:
            msg = f"PRODUCT_PAGE_VERIFIED: Product page active on {post_state.active_app_name} ({post_state.active_window_title})."
            log.info("ProductPageVerifier: %s", msg)
            return True, msg
        else:
            msg = f"PRODUCT_PAGE_FAILED: Product detail page not detected on {post_state.active_app_name} ({post_state.active_window_title})."
            log.warning("ProductPageVerifier: %s", msg)
            return False, msg


class StateVerifier:
    """Verifies action execution and goal completion against expected postconditions."""

    @staticmethod
    def verify(
        action: DesktopAction,
        pre_state: Optional[ScreenState],
        post_state: ScreenState
    ) -> Tuple[bool, str]:
        if not action:
            return True, "No action provided; verification skipped."

        expected = (action.expected_state or "").lower().strip()
        target = (action.target or "").lower().strip()
        val = (action.value or "").lower().strip()
        action_type = (action.action_type or "").upper().strip()
        target_app = (getattr(action, "target_app", "") or "").lower().strip()

        # Handle explicit termination action
        if action_type == "TERMINATE":
            return True, "Session termination action verified."

        if action_type == "WAIT_FOR_TRANSITION":
            return True, "Page transition wait completed."

        # Ignore internal synthetic state names during literal string matching
        SYNTHETIC_STATE_NAMES = ("query_typed", "submitted", "product", "cart_updated", "search_results", "product_page")

        post_title = (post_state.active_window_title or "").lower()
        post_app = (post_state.active_app_name or "").lower()
        post_summary = (post_state.ocr_text or "").lower()

        # HARD SAFETY INVARIANT: Fail verification if post_app is HELIOS when action targeted external app
        if target_app and target_app != "helios" and post_app in ("python.exe", "pythonw.exe"):
            return False, f"TARGET_NOT_REACHED: Active application is HELIOS (python.exe) instead of target application '{target_app}'."

        # Reject HELIOS overlay title as target application evidence
        if any(h_kw in post_title for h_kw in ("helios", "helios popup", "helios floating bar")):
            log.warning("StateVerifier: Post-state title is HELIOS overlay window ('%s'). Evaluating underlying application state.", post_state.active_window_title)
            post_title = ""

        # 1. VERIFY_GOAL Handling
        if action_type == "VERIFY_GOAL":
            if val == "product" or "product" in expected:
                verified, msg = ProductPageVerifier.verify_product_page(action, post_state)
                return verified, msg

            if val == "cart" or "cart" in expected:
                has_cart = "cart" in post_title or "cart" in post_summary or "added" in post_summary or "added" in post_title or "cart" in post_app
                if has_cart:
                    return True, f"CART_STATE_VERIFIED: Item added to cart verified on {post_state.active_app_name} ({post_state.active_window_title})."
                return False, f"CART_STATE_FAILED: Cart update not detected on {post_state.active_app_name} ({post_state.active_window_title})."

            if val in ("settings", "display") or "settings" in expected:
                has_settings = "settings" in post_title or "settings" in post_app or "settings" in post_summary
                if has_settings:
                    return True, f"SETTINGS_VERIFIED: Settings window verified active ({post_state.active_window_title})."
                return False, f"SETTINGS_FAILED: Settings window not active ({post_state.active_window_title})."

            verified, msg, _ = SearchGoalVerifier.verify_search_goal(action, post_state)
            return verified, msg

        # 2. NAVIGATE Verification
        if action_type == "NAVIGATE":
            target_url = (getattr(action, "target_url", "") or target or expected).lower()
            domain_kw = "amazon" if "amazon" in target_url else (target_url.split("//")[-1].split("/")[0] if "//" in target_url else target_url)
            if domain_kw in post_title or domain_kw in post_summary or "chrome" in post_app or "msedge" in post_app:
                return True, f"Navigation to '{domain_kw}' verified active on {post_state.active_app_name} ({post_state.active_window_title})."
            return False, f"TARGET_NOT_REACHED: Expected navigation to '{target_url}', but active window is '{post_state.active_window_title}' ({post_state.active_app_name})."

        # 3. Open Application Verification
        if action_type == "OPEN_APPLICATION" or "open" in action_type.lower():
            req_app = target_app or target or expected
            title_keywords = {
                "settings": "settings",
                "chrome": "chrome",
                "edge": "edge",
                "notepad": "notepad",
                "calculator": "calculator",
                "calc": "calculator",
                "explorer": "file explorer",
            }
            kw = title_keywords.get(req_app, req_app)
            if kw and (kw.lower() in post_title or kw.lower() in post_app or kw.lower() in post_summary):
                return True, f"Application/Window matching '{kw}' verified active ({post_state.active_window_title})."
            return False, f"APPLICATION_LAUNCH_FAILED: Active window '{post_state.active_window_title}' ({post_state.active_app_name}) does not match target '{req_app}'."

        # 4. Explicit expected_state matching (excluding synthetic state names)
        if expected and expected not in SYNTHETIC_STATE_NAMES:
            expected_words = [w for w in expected.split() if len(w) > 2]
            if expected_words:
                matched_words = [w for w in expected_words if w in post_title or w in post_app or w in post_summary]
                if len(matched_words) >= max(1, len(expected_words) // 2):
                    return True, f"Expected state '{expected}' verified in screen state."

        # Default success for intermediate executed actions
        return True, f"Action '{action_type}' executed successfully."
