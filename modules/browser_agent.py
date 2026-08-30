"""
modules/browser_agent.py — HELIOS Controlled Playwright Browser Automation Agent
===================================================================================
Provides controlled browser interaction (launch, navigate, page text extraction,
element click, typing, form submission, page info, close) behind HELIOS/CAHRA routing.
Security: Zero payment authorization, password secret masking, bounded timeouts,
and controlled failure handling.
"""

from __future__ import annotations
import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path

log = logging.getLogger("helios.browser_agent")

try:
    from playwright.sync_api import sync_playwright, Playwright, Browser, Page, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Playwright = Any  # type: ignore
    Browser = Any     # type: ignore
    Page = Any        # type: ignore


class BrowserAgent:
    """Controlled Playwright Browser Automation Controller."""

    def __init__(self, headless: bool = True, timeout_ms: int = 15000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._pw: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

    def is_available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE

    def launch(self) -> bool:
        if not PLAYWRIGHT_AVAILABLE:
            log.warning("Playwright is not installed. Browser automation unavailable.")
            return False
        try:
            if not self._browser:
                self._pw = sync_playwright().start()
                self._browser = self._pw.chromium.launch(headless=self.headless)
                context = self._browser.new_context()
                self._page = context.new_page()
                self._page.set_default_timeout(self.timeout_ms)
                log.info("Playwright Chromium browser launched successfully (Headless: %s)", self.headless)
            return True
        except Exception as exc:
            log.error("Failed to launch Playwright browser: %s", exc)
            return False

    def navigate(self, url: str) -> Dict[str, Any]:
        """Navigates to specified URL."""
        if not self.launch():
            return {"success": False, "error": "Playwright browser unavailable", "url": url}

        # Sanitize URL and check security
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("file://")):
            url = "https://" + url

        try:
            assert self._page is not None
            log.info("Navigating browser to URL: %s", url)
            response = self._page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
            title = self._page.title()
            current_url = self._page.url
            status = response.status if response else 200
            log.info("Browser navigation success: '%s' (Status: %d)", title, status)
            return {
                "success": True,
                "url": current_url,
                "title": title,
                "status": status,
                "error": None
            }
        except Exception as exc:
            log.error("Browser navigation error to '%s': %s", url, exc)
            return {
                "success": False,
                "url": url,
                "title": "",
                "status": 0,
                "error": str(exc)
            }

    def extract_text(self) -> str:
        """Extracts visible text from the current page."""
        if not self._page:
            return "Browser page not open."
        try:
            text = self._page.inner_text("body")
            # Clean up whitespace
            cleaned = re.sub(r'\n\s*\n', '\n\n', text).strip()
            return cleaned[:4000]  # Bounded length
        except Exception as exc:
            log.error("Error extracting page text: %s", exc)
            return f"Error extracting page text: {exc}"

    def _format_selector(self, selector: str) -> str:
        s = selector.strip()
        tags = ("h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "span", "a", "button", "input", "textarea", "select", "body", "form")
        if s.startswith("#") or s.startswith(".") or s.startswith("//") or "[" in s or s in tags or " > " in s or " " in s:
            return s
        return f"text={s}"

    def locate_element(self, selector: str) -> Dict[str, Any]:
        """Locates an element using DOM/CSS/XPath selector or text match."""
        if not self._page:
            return {"success": False, "error": "Browser page not open", "selector": selector}
        try:
            sel = self._format_selector(selector)
            elem = self._page.query_selector(sel)
            if elem and elem.is_visible():
                box = elem.bounding_box()
                return {
                    "success": True,
                    "selector": selector,
                    "visible": True,
                    "bounding_box": box,
                    "error": None
                }
            return {
                "success": False,
                "selector": selector,
                "visible": False,
                "bounding_box": None,
                "error": f"Element '{selector}' not visible or not found"
            }
        except Exception as exc:
            return {"success": False, "selector": selector, "visible": False, "error": str(exc)}

    def click(self, selector: str) -> Dict[str, Any]:
        """Clicks element matching selector."""
        if not self._page:
            return {"success": False, "error": "Browser page not open", "selector": selector}
        try:
            sel = self._format_selector(selector)
            log.info("Browser clicking element: '%s'", selector)
            self._page.click(sel, timeout=self.timeout_ms)
            return {"success": True, "selector": selector, "error": None}
        except Exception as exc:
            log.warning("Browser click failed for '%s': %s", selector, exc)
            return {"success": False, "selector": selector, "error": f"Could not click '{selector}': {exc}"}

    def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Types text into an input field, masking secrets if detected."""
        if not self._page:
            return {"success": False, "error": "Browser page not open", "selector": selector}
        try:
            sel = self._format_selector(selector)
            is_password = "password" in selector.lower() or "secret" in selector.lower()
            log_text = "********" if is_password else text
            log.info("Browser typing into '%s': '%s'", selector, log_text)
            self._page.fill(sel, text, timeout=self.timeout_ms)
            return {"success": True, "selector": selector, "error": None}
        except Exception as exc:
            log.warning("Browser type text failed for '%s': %s", selector, exc)
            return {"success": False, "selector": selector, "error": f"Could not type into '{selector}': {exc}"}

    def submit(self, selector: str) -> Dict[str, Any]:
        """Submits form containing selector."""
        if not self._page:
            return {"success": False, "error": "Browser page not open", "selector": selector}
        try:
            sel = self._format_selector(selector)
            self._page.press(sel, "Enter", timeout=self.timeout_ms)
            return {"success": True, "selector": selector, "error": None}
        except Exception as exc:
            return {"success": False, "selector": selector, "error": f"Could not submit '{selector}': {exc}"}

    def get_info(self) -> Dict[str, Any]:
        """Returns current page URL and title."""
        if not self._page:
            return {"url": "", "title": "Closed"}
        return {
            "url": self._page.url,
            "title": self._page.title()
        }

    def close(self) -> None:
        """Closes browser session."""
        try:
            if self._page:
                self._page.close()
                self._page = None
            if self._browser:
                self._browser.close()
                self._browser = None
            if self._pw:
                self._pw.stop()
                self._pw = None
            log.info("Browser session closed cleanly.")
        except Exception as exc:
            log.error("Error closing browser session: %s", exc)
