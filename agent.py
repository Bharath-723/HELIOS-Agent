"""
HELIOS - Agent Orchestrator  (production-stable)
Python 3.10 compatible.

Design guarantees:
  - process() never raises — all exceptions are caught and returned as strings
  - Every state machine (confirmation, flow, disambiguation) is self-resetting
  - Robust logging throughout
  - open_app("explorer") / "open file explorer" → desktop.open_explorer()
"""

import os
import re
import logging
import shutil
import subprocess
import webbrowser
import urllib.parse
import psutil
import atexit
from datetime import datetime
from pathlib import Path

from core.llm_engine import HybridLLM
from core.nl_router import NLRouter
from modules.desktop_agent import DesktopAgent
from modules.system_controls import SystemControls
from modules.file_creator import FileCreator
from modules.gmail_composer import GmailComposer
from modules.notes_manager import NotesManager
from modules.task_scheduler import TaskScheduler
from modules.web_search import WebSearch
from modules.chat_history import ChatHistory

# ── Logger ────────────────────────────────────────────────────────────────────
log_path = Path(__file__).parent / "helios.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),                            # console
        logging.FileHandler(log_path, encoding="utf-8"),    # file
    ],
)
log = logging.getLogger("helios.agent")

# ── Constants ─────────────────────────────────────────────────────────────────
HELIOS_CHAT = """You are HELIOS, an autonomous desktop AI assistant.
Be concise, helpful, and friendly.
For knowledge questions (recipes, how-to, history, science) give a clear
structured answer then offer ONE helpful follow-up action.
Never say you cannot do something you are actually capable of.

CRITICAL: You CANNOT perform browser automation, click web elements, fill out forms, login to websites, or add items to carts in real-time. If a user asks you to do these, explain clearly and politely that you can only open the page or search for the item, and they must click or log in themselves. Never pretend or lie that you have added an item to a cart or completed a login.
"""

DANGEROUS_ACTIONS: set = {"shutdown", "restart", "empty_recycle", "kill_app"}

# ── Pre-routing pattern guards ────────────────────────────────────────────────
import re as _re

# Pure date patterns: 06-10-2026, 2026/07/12, 12.07.2026 etc. → general_chat
_DATE_PATTERNS = [
    _re.compile(r'^\d{1,2}[\-/\.]\d{1,2}[\-/\.]\d{2,4}$'),   # DD-MM-YYYY
    _re.compile(r'^\d{4}[\-/\.]\d{1,2}[\-/\.]\d{1,2}$'),     # YYYY-MM-DD
    _re.compile(r'^\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}$', _re.I),
]

# Voice STT garbage detector: multi-word input with avg word length < 3.5
# or contains obvious STT noise combos.
_VOICE_NOISE_PHRASES = frozenset([
    "wedding same wrong answers", "wedding wrong answers",
    "heading same wrong", "reading same wrong",
])

_home = Path.home()
_onedrive = _home / "OneDrive"
LOCATIONS: dict = {}
for _folder in ["desktop", "documents", "downloads", "music", "pictures", "videos"]:
    _cap = _folder.capitalize()
    if _onedrive.is_dir() and (_onedrive / _cap).is_dir():
        LOCATIONS[_folder] = _onedrive / _cap
    else:
        LOCATIONS[_folder] = _home / _cap
LOCATIONS["home"] = _home

FOOD_PLATFORMS: dict = {
    "swiggy": "https://www.swiggy.com/search?query={}",
    "zomato": "https://www.zomato.com/search?q={}",
}

MOVIE_PLATFORMS: dict = {
    "bookmyshow": "https://in.bookmyshow.com/search?q={}",
    "paytm":      "https://movies.paytm.com/movies?q={}",
}

# Explorer-intent keywords: any of these → desktop.open_explorer()
EXPLORER_KEYWORDS: set = {
    "explorer", "file explorer", "my computer", "this pc",
    "windows explorer", "open explorer", "file manager",
}


def _ps(cmd: str, timeout: int = 20) -> tuple:
    """Run a PowerShell command, return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as exc:
        return -1, "", str(exc)


def _safe_int(val, default: int) -> int:
    try:
        if val is None:
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


def _is_contained(path: Path, base: Path) -> bool:
    try:
        return path.resolve().is_relative_to(base.resolve())
    except AttributeError:
        try:
            path.resolve().relative_to(base.resolve())
            return True
        except ValueError:
            return False


# ═════════════════════════════════════════════════════════════════════════════
class HELIOSAgent:
    """
    Central orchestrator.  Call process(user_input) → str.
    Never raises; all errors are returned as user-visible strings.
    """

    def __init__(self):
        log.info("Initializing HELIOS agent …")
        self.llm       = HybridLLM()
        self.router    = NLRouter(self.llm)
        self.desktop   = DesktopAgent()
        self.sysctrl   = SystemControls()
        self.files     = FileCreator()
        self.gmail     = GmailComposer()
        self.notes     = NotesManager(self.llm)
        self.scheduler = TaskScheduler()
        self.search    = WebSearch(self.llm)
        from core.payments import HeliosPaymentAdapter
        self.payments  = HeliosPaymentAdapter()
        from core.commerce import CommerceOrchestrator, CommerceTransactionBridge
        self.commerce  = CommerceOrchestrator(CommerceTransactionBridge(self.payments))
        from core.desktop_session import DesktopSessionManager
        self.session_manager = DesktopSessionManager(
            desktop=self.desktop, sysctrl=self.sysctrl, commerce=self.commerce, llm=self.llm
        )
        self.history   = ChatHistory()
        self._shutdown_done = False
        atexit.register(self.shutdown)

        # ── State machines ────────────────────────────────────────────────
        self._pending_action: str | None = None
        self._pending_params: dict       = {}
        self._pending_raw:   str         = ""

        self._flow:      str | None = None   # "order_food" | "book_movie"
        self._flow_data: dict       = {}

        self._last_draft: str = ""           # email draft carry-forward

        # Disambiguation
        self._disambig_items:  list      = []
        self._disambig_action: str | None = None
        self._disambig_kw:     str        = ""
        
        # Search results state carry-forward for flow continuation
        self._last_search_results: list = []

        # UI reminder callback (set by popup after init)
        self._ui_notify_cb = None
        self.scheduler.set_notify_callback(self._on_reminder)

        # Screen Context Toggle State (Default: OFF)
        self._screen_context_enabled = False
        self.last_used_model = "gemma3"

        log.info("HELIOS ready.")

    # ── External wiring ───────────────────────────────────────────────────────
    def set_screen_context_enabled(self, enabled: bool) -> None:
        """User explicit Screen Context Toggle (OFF / ON)."""
        self._screen_context_enabled = bool(enabled)
        log.info("HELIOSAgent: Screen context toggle set to %s", self._screen_context_enabled)
        if not self._screen_context_enabled:
            # Immediately terminate persistent desktop session & clear frame buffers
            if hasattr(self, "session_manager") and self.session_manager:
                self.session_manager.end_session(reason="Screen Context disabled by user")

    def set_ui_notify(self, cb):
        """Called by helios_popup to push reminders into the chat window."""
        self._ui_notify_cb = cb
        log.info("UI notify callback registered.")

    def _on_reminder(self, msg: str):
        """Fired by TaskScheduler when a reminder is due."""
        log.info("Reminder fired: %s", msg)
        self.history.add("helios", msg)
        if self._ui_notify_cb:
            try:
                self._ui_notify_cb(msg)
            except Exception as exc:
                log.warning("UI notify callback error: %s", exc)

    # ═════════════════════════════════════════════════════════════════════
    # PUBLIC ENTRY POINT
    # ═════════════════════════════════════════════════════════════════════
    def process(self, user_input: str) -> str:
        """
        Main entry point.  Always returns a str, never raises.
        """
        try:
            return self._process_impl(user_input)
        except Exception as exc:
            log.error("process() unhandled exception: %s", exc, exc_info=True)
            return f"Unexpected error: {exc}\n(See helios.log for details)"

    def _resolve_search_selection(self, text: str) -> str | None:
        inp = text.lower().strip()
        
        # 1. Check if it's a number directly
        if inp.isdigit():
            idx = int(inp) - 1
            if 0 <= idx < len(self._last_search_results):
                return self._last_search_results[idx]
                
        # 2. Check for ordinal words
        ordinals = {
            "first": 0, "1st": 0, "one": 0, "that": 0, "that video": 0, "the video": 0,
            "second": 1, "2nd": 1, "two": 1,
            "third": 2, "3rd": 2, "three": 2,
            "fourth": 3, "4th": 3, "four": 3,
            "fifth": 4, "5th": 4, "five": 4,
        }
        for word, idx in ordinals.items():
            if word == inp or f"play {word}" in inp or f"open {word}" in inp or f"{word} one" in inp or f"the {word}" in inp:
                if 0 <= idx < len(self._last_search_results):
                    return self._last_search_results[idx]
                    
        # 3. Check for partial name match
        matches = [p for p in self._last_search_results if inp in Path(p).name.lower()]
        if len(matches) == 1:
            return matches[0]
            
        return None

    def _process_impl(self, user_input: str) -> str:
        text = user_input.strip()
        if not text:
            return "Please enter a command."

        log.info("User: %s", text)
        self.history.add("user", text)

        # ── Pre-routing guards ──────────────────────────────────────────────
        # Guard 0: Direct Real-Time Date & Time Queries
        lower_raw = text.lower().strip()
        if lower_raw in [
            "today date", "today's date", "what is today date", "what is today's date",
            "current date", "what is the date today", "what date is it", "date today", "date"
        ]:
            now = datetime.now()
            today_str = now.strftime("%A, %B %d, %Y")
            result = f"Today is **{today_str}**.\n\nWould you like me to check your schedule or set a reminder for today?"
            self.history.add("helios", result)
            return result

        if lower_raw in ["time", "current time", "what time is it", "what is the time", "time now", "tell me the time"]:
            now = datetime.now()
            time_str = now.strftime("%I:%M %p")
            result = f"The current time is **{time_str}**."
            self.history.add("helios", result)
            return result

        # Guard 0.5: Deep File Search & Spiderman / Movie queries
        if any(kw in lower_raw for kw in ("movie", "spiderman", "downloaded", "where is", "where got it save", "saved")):
            if any(kw in lower_raw for kw in ("search", "find", "where", "downloaded", "movie", "play", "saved")):
                log.info("Pre-routing guard: Deep File Search query detected '%s'", text)
                result = self.desktop.deep_file_search(text)
                self.history.add("helios", result)
                return result

        # Guard 0.55: Product Link Guard — NEVER open a merchant search URL as Product Link
        if lower_raw in ("product link", "show product link", "open product link", "get product link", "link"):
            log.info("Pre-routing guard: Product Link request detected '%s'", text)
            last_context = getattr(self.commerce, "_last_context", None)
            cand = None
            if last_context and last_context.recommendation:
                cand = last_context.recommendation.selected_candidate

            if cand and cand.direct_product_url and cand.classification == "DIRECT_PRODUCT_PAGE":
                result = self.desktop.open_website(cand.direct_product_url)
                self.history.add("helios", result)
                return result
            elif cand and cand.source_url:
                from core.commerce.search.result_classifier import ResultClassifier
                url_cls = ResultClassifier.classify(cand.source_url)
                if url_cls in ("MERCHANT_SEARCH_PAGE", "MERCHANT_COLLECTION", "CATEGORY_PAGE"):
                    result = (
                        f"⚠️ **Product Link Pending Verification**:\n"
                        f"The discovered merchant result at {cand.merchant} is a search/collection page ({cand.source_url}) "
                        f"rather than a direct product page.\n"
                        f"HELIOS cannot expose search URLs as official product links. Secondary research is required to resolve the direct product page."
                    )
                    self.history.add("helios", result)
                    return result

            result = "⚠️ No verified direct product page link is available for the current item."
            self.history.add("helios", result)
            return result

        # Commerce Indicators check
        _COMMERCE_INDICATORS = ("under ₹", "under rs", "for ₹", "buy the best", "compare these", "don't buy", "dont buy", "make the payment", "checkout", "buy this", "pay ₹")
        _is_comm = any(re.search(r'\b' + re.escape(v) + r'\b', lower_raw) for v in ("pay", "buy", "purchase", "checkout")) or any(kw in lower_raw for kw in _COMMERCE_INDICATORS)
        _is_pure_info = lower_raw.startswith("what is the price") or "previous payments" in lower_raw or "payment history" in lower_raw

        # Class B Visual / Screen-Dependent Interaction Keywords
        _CLASS_B_KEYWORDS = (
            "select the first", "click the first", "choose the first", "choose first", "click first", "select first",
            "add the first product", "add first product", "add to cart", "click add to cart", "add the product to cart",
            "open cart", "open the cart", "click checkout", "click the checkout button",
            "click the button", "click button on screen", "select option", "click option",
            "on the shorts", "on shorts", "click shorts", "click on", "clcikn on", "clcikn", "clik on"
        )
        _is_click_action = bool(re.search(r'\b(click|clcik|clcikn|clik|tap|press|select|choose)\b', lower_raw))
        _is_class_b = any(kw in lower_raw for kw in _CLASS_B_KEYWORDS) or (_is_click_action and not lower_raw.startswith("http"))

        # Class A System / Application Launch & Control Keywords (No screen observation required)
        _is_class_a = any(lower_raw.startswith(kw) for kw in (
            "open chrome", "launch chrome", "open settings", "open display", "open notepad",
            "open calculator", "launch vs code", "open vscode", "open explorer", "close chrome",
            "kill notepad", "open bluetooth", "open wifi"
        ))

        # Check Class B requests when Screen Context is OFF
        if _is_class_b and not self._screen_context_enabled:
            log.info("Class B visual interaction requested while Screen Context is OFF '%s'", text)
            result = "Screen Context is required for this visual interaction.\nEnable it beside the model selector and retry."
            self.history.add("helios", result)
            return result

        # Guard 0.58: Persistent Screen-Aware Desktop Session Guard (only for active session or authorized Class B)
        from core.desktop_session import TaskContinuityEngine, DesktopSessionState
        _is_session_term = TaskContinuityEngine.is_termination_request(text)
        _in_active_session = self.session_manager.get_current_context().session_state in (DesktopSessionState.WAITING_FOR_USER, DesktopSessionState.ACTIVE)

        if (_is_session_term or (_in_active_session and self._screen_context_enabled and not _is_comm) or (_is_class_b and self._screen_context_enabled and not _is_comm)) and not _is_class_a:
            log.info("Pre-routing guard: Desktop session instruction detected '%s'", text)
            sess_res = self.session_manager.process_instruction(text)

            if sess_res.get("permission_required"):
                result = sess_res.get("message")
                self.history.add("helios", result)
                return result

            if sess_res.get("permission_denied"):
                result = (
                    f"⚠️ **Screen Access Denied**:\n"
                    f"The selected cloud model needs screen access to continue this task, but screen access was denied by user.\n"
                    f"No screenshot or OCR context was transmitted to the cloud model."
                )
                self.history.add("helios", result)
                return result

            if sess_res.get("success"):
                action_info = sess_res.get("action_executed") or {}
                ver_reason = sess_res.get("verification_reason") or "Verified"
                state_str = sess_res.get("state")
                app_str = sess_res.get("active_application") or "Desktop"
                result = (
                    f"🖥️ **Desktop Agent Session** [{state_str}]:\n"
                    f"**Action**: {action_info.get('action_type', 'Action')} ({action_info.get('target', '')})\n"
                    f"**Active App**: {app_str}  |  **Verification**: {ver_reason}\n"
                    f"**Status**: Waiting for your next instruction..."
                )
                self.history.add("helios", result)
                return result
            else:
                msg = sess_res.get("message") or "Desktop action failed verification."
                result = f"⚠️ {msg}\n\n**Status**: Waiting for your next instruction..."
                self.history.add("helios", result)
                return result

        # Guard 0.6: End-to-End Agentic Commerce & Payment Intents
        if _is_comm and not _is_pure_info:
            log.info("Pre-routing guard: Commercial intent detected '%s'", text)
            comm_res = self.commerce.process_commerce_request(text)
            if comm_res.get("success"):
                if comm_res.get("type") in ("COMMERCE_TRANSACTION_READY", "PAYMENT_ONLY"):
                    import json
                    result = "COMMERCE_INTENT_JSON:" + json.dumps(comm_res)
                    self.history.add("helios", result)
                    return result
                elif comm_res.get("type") == "INFORMATION_ONLY":
                    ctx = comm_res.get("context", {})
                    rec = ctx.get("recommendation") or {}
                    cand = rec.get("selected_candidate") or {}
                    
                    # Live Display Rule: Display (LIVE) ONLY if direct page verified; otherwise (Search-result price)
                    is_verified = (cand.get("verification_status") == "DIRECT_PAGE_VERIFIED" or cand.get("price_type") == "LIVE_PRODUCT_PAGE")
                    price_badge = "LIVE Verified" if is_verified else "Search-result price"

                    offers_str = ""
                    if cand.get("merchant_offers"):
                        offers_str = "\n**Merchant Offer Comparison**:\n" + "\n".join(
                            f"  • {off.get('merchant')}: ₹{off.get('price_inr'):,.2f} ({( 'LIVE' if off.get('verification_status') == 'DIRECT_PAGE_VERIFIED' else 'Search-result price' )})"
                            for off in cand.get("merchant_offers")[:3]
                        ) + "\n"

                    # Product Link Rule: Never open search URL as Product Link
                    direct_url = cand.get("direct_product_url")
                    link_str = f"\n**Product Link**: [View Verified Product Page]({direct_url})" if direct_url else "\n*(Direct product page link pending verification)*"

                    result = (
                        f"🛍️ **Research & Recommendation for {ctx.get('intent', {}).get('target_item', 'Requested Item')}**:\n\n"
                        f"**Recommended**: {cand.get('name', 'Product')}\n"
                        f"**Price**: ₹{cand.get('price_inr', 0.0):,.2f} ({price_badge})  |  **Merchant**: {cand.get('merchant', 'Partner Store')}\n"
                        f"{link_str}\n"
                        f"{offers_str}\n"
                        f"**Reason**: {rec.get('reason', '')}\n\n"
                        f"*(No transaction prepared per your request)*"
                    )
                    self.history.add("helios", result)
                    return result
            else:
                err_msg = comm_res.get("error_message") or "HELIOS couldn't retrieve reliable current prices from available sources."
                result = f"⚠️ {err_msg}\n\n[ Retry Research ]"
                self.history.add("helios", result)
                return result

        # Guard 1: Pure date string → always general_chat (never list_folder)
        text_stripped = text.strip()
        if any(p.match(text_stripped) for p in _DATE_PATTERNS):
            log.info("Pre-routing guard: date pattern detected '%s' → general_chat", text_stripped)
            resp = self.llm.chat(
                prompt=f"The user entered a date: {text_stripped}. What would you like to do with this date?",
                system=self._get_system_prompt())
            result = resp.content + f"\n(via {resp.model})"
            self.history.add("helios", result)
            return result

        # Guard 2: Voice STT garbage filter — detect known noise phrases
        # or statistically incoherent multi-word inputs (avg word len < 3)
        text_lower = text_stripped.lower()
        if text_lower in _VOICE_NOISE_PHRASES:
            log.warning("Pre-routing guard: voice STT noise detected '%s'", text_stripped)
            result = ("⚠ I didn't catch that clearly — the voice input may have been garbled.\n"
                     "Please try again or type your command.")
            self.history.add("helios", result)
            return result
        words = text_stripped.split()
        if (len(words) >= 3
                and all(len(w) >= 2 for w in words)   # not single-char fragments
                and sum(len(w) for w in words) / len(words) < 3.2
                and not any(c.isdigit() for c in text_stripped)):
            # Very short average word length → likely STT noise
            log.warning("Pre-routing guard: possible STT noise (avg word len=%.1f) '%s'",
                        sum(len(w) for w in words) / len(words), text_stripped)
            result = ("⚠ That didn't come through clearly.\n"
                     "Could you rephrase or type what you meant?")
            self.history.add("helios", result)
            return result
        # ── End pre-routing guards ──────────────────────────────────────────

        # Priority 1: disambiguation waiting
        if self._disambig_items:
            result = self._handle_disambig(text)
            self.history.add("helios", result)
            return result

        # Priority 2: dangerous-action confirmation waiting
        if self._pending_action:
            result = self._handle_confirmation(text)
            self.history.add("helios", result)
            return result

        # Priority 3: multi-step flow active
        if self._flow:
            result = self._continue_flow(text)
            self.history.add("helios", result)
            return result

        # Priority 3.5: resolve selection from last search results
        if self._last_search_results:
            resolved = self._resolve_search_selection(text)
            if resolved:
                action_to_take = "play" if any(w in text.lower() for w in ("play", "stream", "watch", "listen", "run")) else "open"
                result = self._exec_on_chosen(resolved, action_to_take, "")
                log.info("Resolved search selection → playing/opening: %s", resolved)
                self._last_search_results = []  # clear results
                self.history.add("helios", result)
                return result

        # Priority 4: normal routing
        parsed = self.router.parse(text, self._get_context())
        action = parsed.get("action", "general_chat")
        params = parsed.get("params", {}) or {}
        log.info("Routed → action=%s params=%s", action, params)

        # Post-routing sanity: date accidentally mapped to list_folder → fix
        if action == "list_folder" and any(p.match(text_stripped) for p in _DATE_PATTERNS):
            log.warning("Post-routing guard: date '%s' mis-routed to list_folder → redirecting to general_chat",
                        text_stripped)
            action = "general_chat"
            params = {"message": text_stripped}

        if action in DANGEROUS_ACTIONS:
            self._pending_action = action
            self._pending_params = params
            self._pending_raw    = text
            msg = self._confirmation_prompt(action, params)
            self.history.add("helios", msg)
            return msg

        result = self._execute(action, params, text)
        if result is None:
            log.warning("Action '%s' returned None -> falling back to general_chat", action)
            resp = self.llm.chat(prompt=self._chat_prompt(text), system=self._get_system_prompt())
            result = f"{resp.content}\n(via {resp.model})"

        log.info("Result: %s", str(result)[:120].replace("\n", " "))
        self.history.add("helios", result)
        return result

    # ═════════════════════════════════════════════════════════════════════
    # CONTEXT
    # ═════════════════════════════════════════════════════════════════════
    def _get_context(self) -> str:
        msgs = self.history.messages[-6:]
        return "\n".join(
            f"{'User' if m['role'] == 'user' else 'HELIOS'}: {m['content'][:300]}"
            for m in msgs
        )

    def _chat_prompt(self, message: str) -> str:
        ctx = self._get_context()
        if not ctx:
            return message
        # Trim context: remove large file listing dumps to prevent context bleed
        # into general_chat LLM responses (e.g. "Files in Downloads:" etc.)
        ctx_lines = ctx.splitlines()
        clean_lines = []
        skip = False
        for line in ctx_lines:
            stripped = line.strip()
            # Start skipping when we see a folder listing header
            if _re.search(r'^HELIOS:.*Files in .+\(\d+ total\)', stripped):
                skip = True
                clean_lines.append("HELIOS: [folder listing - hidden from chat context]")
                continue
            # Stop skipping at next User/HELIOS turn (not a file bullet)
            if skip and (stripped.startswith("User:") or stripped.startswith("HELIOS:")):
                skip = False
            if not skip:
                clean_lines.append(line)
        ctx = "\n".join(clean_lines)
        return f"Conversation:\n{ctx}\n\nUser: {message}"

    # ═════════════════════════════════════════════════════════════════════
    # CONFIRMATION FLOW
    # ═════════════════════════════════════════════════════════════════════
    def _confirmation_prompt(self, action: str, p: dict) -> str:
        labels = {
            "shutdown":      "SHUT DOWN the computer",
            "restart":       "RESTART the computer",
            "empty_recycle": "permanently EMPTY the Recycle Bin",
            "kill_app":      f"force-close '{p.get('app', 'the app')}'",
        }
        label = labels.get(action, f"perform '{action}'")
        return f"⚠ Are you sure you want to {label}?\nReply 'yes' to confirm or 'no' to cancel."

    def _handle_confirmation(self, text: str) -> str:
        YES = {"yes", "y", "yeah", "yep", "ok", "okay", "sure", "confirm", "do it", "proceed"}
        NO  = {"no",  "n", "nope", "cancel", "stop", "abort"}
        inp = text.lower().strip()

        action = self._pending_action
        p      = self._pending_params
        raw    = self._pending_raw
        # Reset state unconditionally
        self._pending_action = None
        self._pending_params = {}
        self._pending_raw    = ""

        if any(w in inp for w in YES):
            log.info("Confirmation YES for action=%s", action)
            return self._execute(action, p, raw)
        if any(w in inp for w in NO):
            log.info("Confirmation NO for action=%s", action)
            return f"Cancelled — '{action}' was not executed."
        # Unclear: re-ask (restore state)
        self._pending_action = action
        self._pending_params = p
        self._pending_raw    = raw
        return "Please reply 'yes' to confirm or 'no' to cancel."

    # ═════════════════════════════════════════════════════════════════════
    # DISAMBIGUATION FLOW
    # ═════════════════════════════════════════════════════════════════════
    def _ask_disambig(self, items: list, action: str, keyword: str = "") -> str:
        self._disambig_items  = items
        self._disambig_action = action
        self._disambig_kw     = keyword
        lines = [f"Found {len(items)} matching files — which one?\n"]
        for i, path in enumerate(items[:8], 1):
            lines.append(f"  {i}. {Path(path).name}  [{Path(path).parent}]")
        lines.append("\nReply with the number or part of the filename.")
        return "\n".join(lines)

    def _handle_disambig(self, text: str) -> str:
        items  = self._disambig_items
        action = self._disambig_action
        kw     = self._disambig_kw
        # Always reset state first
        self._disambig_items  = []
        self._disambig_action = None
        self._disambig_kw     = ""

        inp = text.strip()
        chosen = None

        if inp.isdigit():
            idx = int(inp) - 1
            if 0 <= idx < len(items):
                chosen = items[idx]
            else:
                return "Invalid number. Cancelled."
        else:
            matches = [p for p in items if inp.lower() in Path(p).name.lower()]
            if len(matches) == 1:
                chosen = matches[0]
            elif len(matches) == 0:
                return f"No match for '{inp}'. Cancelled."
            else:
                return self._ask_disambig(matches, action, kw)   # re-narrow

        return self._exec_on_chosen(chosen, action, kw)

    def _exec_on_chosen(self, path: str, action: str, kw: str) -> str:
        try:
            if action == "search_in":
                return self.desktop.search_in_file(path, kw)
            if action == "convert_to_pdf":
                return self.files.convert_to_pdf(path)
            os.startfile(path)
            return f"{'Playing' if action == 'play' else 'Opened'}: {Path(path).name}"
        except Exception as exc:
            log.error("exec_on_chosen error: %s", exc, exc_info=True)
            return f"Could not open '{Path(path).name}': {exc}"

    # ═════════════════════════════════════════════════════════════════════
    # MULTI-STEP FLOW ENGINE
    # ═════════════════════════════════════════════════════════════════════
    def _continue_flow(self, text: str) -> str:
        if self._flow == "order_food":
            return self._food_flow_step(text)
        if self._flow == "book_movie":
            return self._movie_flow_step(text)
        # Unknown flow — reset
        self._flow = None
        self._flow_data = {}
        return self._process_impl(text)

    # ── Food ordering ─────────────────────────────────────────────────────────
    def _start_food_flow(self, item: str, platform: str,
                         location: str, budget: str) -> str:
        self._flow = "order_food"
        self._flow_data = {
            "item":     item.strip(),
            "platform": platform.strip().lower(),
            "location": location.strip(),
            "budget":   budget.strip(),
        }
        return self._food_flow_step(None)

    def _food_flow_step(self, reply) -> str:
        d = self._flow_data
        if reply:
            r = reply.strip().lower()
            if not d["platform"]:
                d["platform"] = ("swiggy" if "swiggy" in r else
                                 "zomato"  if "zomato"  in r else r)
            elif not d["location"]:
                d["location"] = reply.strip()
            elif not d["budget"]:
                d["budget"] = reply.strip() if any(c.isdigit() for c in reply) else "any"

        if not d["platform"]:
            return f"Where should I order {d['item'] or 'food'} from?\nReply: Swiggy or Zomato"
        if not d["location"]:
            return f"Got it — {d['platform'].title()}. What's your delivery location?"
        if not d["budget"]:
            return "What's your budget? (e.g. 200, 500, or 'any')"

        return self._open_food_order()

    def _open_food_order(self) -> str:
        d        = self._flow_data
        item     = d.get("item") or "food"
        platform = d.get("platform", "swiggy")
        tmpl     = FOOD_PLATFORMS.get(platform,
                                      f"https://www.{platform}.com/search?q={{}}")
        url = tmpl.format(urllib.parse.quote(item))
        webbrowser.open(url)
        self._flow = None
        self._flow_data = {}
        return (
            f"Opening {platform.title()} for: {item}\n"
            f"  Location: {d['location']}\n"
            f"  Budget:   {d['budget']}\n\n"
            f"{platform.title()} search page is open — pick a restaurant!"
        )

    # ── Movie booking ─────────────────────────────────────────────────────────
    def _start_movie_flow(self, movie: str, platform: str,
                          city: str, date: str) -> str:
        self._flow = "book_movie"
        self._flow_data = {
            "movie":    movie.strip(),
            "platform": platform.strip().lower(),
            "city":     city.strip(),
            "date":     date.strip(),
        }
        return self._movie_flow_step(None)

    def _movie_flow_step(self, reply) -> str:
        d = self._flow_data
        if reply:
            r = reply.strip().lower()
            if not d["platform"]:
                d["platform"] = ("bookmyshow" if "bms" in r or "bookmyshow" in r else
                                 "paytm"       if "paytm"  in r else
                                 "bookmyshow")
            elif not d["city"]:
                d["city"] = reply.strip()
            elif not d["date"]:
                d["date"] = "today" if r == "today" else reply.strip()

        if not d["platform"]:
            return "Which platform?\n  1. BookMyShow\n  2. Paytm Movies"
        if not d["city"]:
            return f"Got it — {d['platform'].title()}. Which city? (e.g. Hyderabad)"
        if not d["date"]:
            return "Which date? (e.g. today, tomorrow, 20 Apr, or 'any')"

        return self._open_movie_booking()

    def _open_movie_booking(self) -> str:
        d        = self._flow_data
        movie    = d.get("movie", "")
        platform = d.get("platform", "bookmyshow")
        city     = d.get("city", "")

        tmpl = MOVIE_PLATFORMS.get(platform,
                                   f"https://www.{platform}.com/search?q={{}}")
        url  = tmpl.format(urllib.parse.quote(movie or city))
        webbrowser.open(url)
        self._flow = None
        self._flow_data = {}
        return (
            f"Opening {platform.title()} for: {movie or 'movies'}\n"
            f"  City: {city}\n"
            f"  Date: {d.get('date', 'any')}\n\n"
            f"Select your theatre, showtime, and seats!"
        )

    # ═════════════════════════════════════════════════════════════════════
    # EXECUTE — central dispatch
    # ═════════════════════════════════════════════════════════════════════
    def _execute(self, action: str, p: dict, raw: str) -> str:  # noqa: C901
        try:
            return self._dispatch(action, p, raw)
        except Exception as exc:
            log.error("_execute('%s') error: %s", action, exc, exc_info=True)
            return f"Error executing '{action}': {exc}"

    def _dispatch(self, action: str, p: dict, raw: str) -> str:  # noqa: C901

        # ── MEDIA ─────────────────────────────────────────────────────────────
        if action == "play_media":
            query   = p.get("query") or raw
            if "youtube" in raw.lower() or "online" in raw.lower():
                log.info("play_media fallback: detected 'youtube'/'online' in prompt. Re-routing to search_youtube.")
                return self.desktop.search_youtube(query, raw_intent=raw)
            matches = self.desktop.play_media(query)
            if isinstance(matches, str):          # error message
                return matches
            if not matches:
                return f"No media found for '{query}'."
            if len(matches) == 1:
                return self._exec_on_chosen(matches[0], "play", "")
            return self._ask_disambig(matches, "play")

        # ── APPS ──────────────────────────────────────────────────────────────
        if action == "open_app":
            app   = (p.get("app") or raw).strip()
            query = p.get("query") or p.get("search") or ""
            # Intercept all explorer-intent strings right here
            if app.lower() in EXPLORER_KEYWORDS or app.lower() == "":
                return self.desktop.open_explorer()
            if query and "explorer" in app.lower():
                return self.desktop.open_explorer_search(query)
            return self.desktop.open_app(app)

        if action == "kill_app":
            return self.desktop.kill_app(p.get("app") or raw)

        if action == "open_website":
            return self.desktop.open_website(p.get("site") or "", query=p.get("query") or "")

        if action == "open_url":
            return self.desktop.open_url(p.get("url") or "")

        if action == "search_google":
            return self.desktop.search_google(p.get("query") or raw)

        if action in ("search_youtube", "open_youtube"):
            query = p.get("query") or raw
            local_kws = ("local", "pc", "computer", "my drive", "my pc", "my files", "my computer", "local computer", "hard drive")
            if any(kw in raw.lower() for kw in local_kws):
                log.info("search_youtube fallback: detected local keywords in prompt. Re-routing to find_file/play_media.")
                if any(w in raw.lower() for w in ("play", "stream", "watch", "listen")):
                    matches = self.desktop.play_media(query)
                    if isinstance(matches, str):
                        return matches
                    if not matches:
                        return f"No media found for '{query}'."
                    if len(matches) == 1:
                        return self._exec_on_chosen(matches[0], "play", "")
                    return self._ask_disambig(matches, "play")
                else:
                    folders = self.desktop.search_folder(query)
                    files   = self.desktop.search_file(query)
                    results = folders + [f for f in files if f not in folders]
                    if not results:
                        self._last_search_results = []
                        return f"Nothing found matching '{query}'."
                    self._last_search_results = results
                    lines = [f"Found {len(results)} matching files:\n"]
                    for i, r in enumerate(results[:15], 1):
                        lines.append(f"  {i}. {Path(r).name}  [{Path(r).parent}]")
                    return "\n".join(lines)
            return self.desktop.search_youtube(query, raw_intent=raw)

        if action == "open_explorer_search":
            return self.desktop.open_explorer_search(p.get("query") or raw)

        if action == "open_explorer":
            return self.desktop.open_explorer(p.get("path") or "")

        # ── FOOD / MOVIES ─────────────────────────────────────────────────────
        if action == "order_food":
            return self._start_food_flow(
                p.get("item", ""), p.get("platform", ""),
                p.get("location", ""), p.get("budget", ""))

        if action == "book_movie":
            return self._start_movie_flow(
                p.get("movie", ""), p.get("platform", ""),
                p.get("city", ""), p.get("date", ""))

        # ── FILES ─────────────────────────────────────────────────────────────
        if action == "convert_to_pdf":
            path = p.get("path") or ""
            if not path:
                query = p.get("query") or raw
                # Only clean stop-words using word boundaries so we do not strip characters from inside filenames
                clean_query = re.sub(r'\b(convert|to|pdf|file|make|a|into)\b', '', query, flags=re.IGNORECASE)
                clean_query = re.sub(r'\s+', ' ', clean_query).strip()
                
                results = self.desktop.search_file(clean_query)
                exact = [r for r in results if Path(r).name.lower() == clean_query.lower()]
                candidates = exact if exact else results
                if not candidates:
                    return f"No file found matching '{clean_query}' to convert to PDF."
                if len(candidates) > 1:
                    return self._ask_disambig(candidates, "convert_to_pdf")
                path = candidates[0]
            return self.files.convert_to_pdf(path)

        if action == "create_file":
            return self.files.create_file(
                name=p.get("name", "helios_file.txt"),
                location=p.get("location", "desktop"),
                content=p.get("content", ""))

        if action == "list_folder":
            return self._list_folder(p.get("location") or p.get("query") or raw)

        if action in ("find_file", "deep_file_search"):
            query = p.get("query") or raw
            return self.desktop.deep_file_search(query)

        if action == "open_file":
            path = p.get("path") or ""
            if path and Path(path).exists():
                try:
                    os.startfile(path)
                    return f"Opened: {Path(path).name}"
                except Exception as exc:
                    return f"Could not open: {exc}"
            return f"File not found: {path}"

        if action == "search_in_file":
            return self._search_in_file(
                p.get("filename") or p.get("file") or "",
                p.get("keyword") or p.get("word") or "")

        if action == "move_file":
            src = p.get("name") or p.get("from") or p.get("file") or raw
            dest = p.get("to") or p.get("destination") or ""
            return self.desktop.move_file(src, dest)

        if action == "copy_file":
            src = p.get("name") or p.get("from") or p.get("file") or raw
            dest = p.get("to") or p.get("destination") or ""
            return self.desktop.copy_file(src, dest)

        if action == "rename_file":
            src = p.get("name") or p.get("from") or p.get("file") or raw
            new_name = p.get("new_name") or p.get("to") or ""
            return self.desktop.rename_file(src, new_name)

        if action == "delete_file":
            target = p.get("path") or p.get("name") or raw
            return self.desktop.delete_file(target)

        # ── EMAIL ─────────────────────────────────────────────────────────────
        if action == "compose_gmail":
            body = p.get("body") or ""
            if not body and self._last_draft:
                body = self._last_draft
            result = self.gmail.compose(
                to=p.get("to", ""), subject=p.get("subject", ""), body=body)
            self._last_draft = ""
            return result

        if action == "open_gmail":
            return self.gmail.open_gmail()

        # ── WIFI ──────────────────────────────────────────────────────────────
        if action == "wifi_on":      return self.sysctrl.wifi_on()
        if action == "wifi_off":     return self.sysctrl.wifi_off()
        if action == "wifi_status":  return self.sysctrl.wifi_status()

        # ── BLUETOOTH ─────────────────────────────────────────────────────────
        if action == "bluetooth_on":  return self.sysctrl.bluetooth_on()
        if action == "bluetooth_off": return self.sysctrl.bluetooth_off()

        # ── AIRPLANE MODE ─────────────────────────────────────────────────────
        if action == "airplane_mode_on":  return self.sysctrl.airplane_mode_on()
        if action == "airplane_mode_off": return self.sysctrl.airplane_mode_off()

        # ── NIGHT LIGHT ───────────────────────────────────────────────────────
        if action == "night_light_on":   return self.sysctrl.night_light_on()
        if action == "night_light_off":  return self.sysctrl.night_light_off()
        if action == "night_light_status": return self.sysctrl.night_light_status()

        # ── MOBILE HOTSPOT ────────────────────────────────────────────────────
        if action == "hotspot_on":       return self.sysctrl.hotspot_on()
        if action == "hotspot_off":      return self.sysctrl.hotspot_off()
        if action == "hotspot_status":   return self.sysctrl.hotspot_status()

        # ── BRIGHTNESS ────────────────────────────────────────────────────────
        if action == "brightness_set":
            return self.sysctrl.set_brightness(_safe_int(p.get("level"), 70))
        if action == "brightness_up":
            return self.sysctrl.brightness_up(_safe_int(p.get("amount"), 10))
        if action == "brightness_down":
            return self.sysctrl.brightness_down(_safe_int(p.get("amount"), 10))

        # ── VOLUME ────────────────────────────────────────────────────────────
        if action == "volume_up":
            return self.desktop.volume_up(_safe_int(p.get("steps"), 5))
        if action == "volume_down":
            return self.desktop.volume_down(_safe_int(p.get("steps"), 5))
        if action == "mute":
            return self.desktop.mute()
        if action == "pause_media":
            return self.desktop.pause_media()
        if action == "stop_media":
            return self.desktop.stop_media()

        # ── SYSTEM ────────────────────────────────────────────────────────────
        if action == "screenshot":         return self.desktop.screenshot()
        if action == "lock_screen":        return self.desktop.lock_screen()
        if action == "shutdown":           return self.desktop.shutdown(_safe_int(p.get("delay"), 0))
        if action == "restart":            return self.desktop.restart()
        if action == "sleep":              return self.desktop.sleep()
        if action == "battery":            return self.desktop.battery_status()
        if action == "disk_space":         return self.desktop.disk_space()
        if action == "system_info":        return self._system_info()
        if action == "running_apps":       return self.desktop.running_apps()
        if action == "ip_address":         return self.desktop.ip_address()
        if action == "empty_recycle":      return self.desktop.empty_recycle()
        if action == "dark_mode_on":       return self.sysctrl.dark_mode_on()
        if action == "dark_mode_off":      return self.sysctrl.dark_mode_off()
        if action == "power_performance":  return self.sysctrl.power_performance()
        if action == "power_balanced":     return self.sysctrl.power_balanced()
        if action == "power_saver":        return self.sysctrl.power_saver()
        if action == "flush_dns":          return self.sysctrl.flush_dns()
        if action == "open_settings":      return self.sysctrl.open_settings(p.get("page", ""))
        if action == "open_task_manager":  return self.sysctrl.open_task_manager()
        if action == "top_processes":      return self.sysctrl.top_processes()

        # ── OLLAMA ────────────────────────────────────────────────────────────
        if action == "ollama_pull":   return self._ollama_pull(p.get("model", ""))
        if action == "ollama_delete": return self._ollama_delete(p.get("model", ""))
        if action == "ollama_list":   return self._ollama_list()

        # ── NOTES ─────────────────────────────────────────────────────────────
        if action == "create_note":
            return self.notes.create(p.get("title", "Untitled"), p.get("content", ""))
        if action == "list_notes":   return self.notes.list_notes()
        if action == "read_note":    return self.notes.read(p.get("title", ""))
        if action == "search_notes": return self.notes.search(p.get("query", raw))

        # ── TASKS ─────────────────────────────────────────────────────────────
        if action == "schedule_task":
            return self.scheduler.schedule(
                p.get("description", raw), p.get("time", "in 1 hour"))
        if action == "list_tasks":   return self.scheduler.list_tasks()
        if action == "cancel_task":  return self.scheduler.cancel_task(p.get("id", ""))

        # ── WEB SEARCH ────────────────────────────────────────────────────────
        if action == "web_search":
            return self.search.search(p.get("query", raw))

        # ── RAZORPAY AGENTIC PAYMENTS ─────────────────────────────────────────
        if action == "razorpay_payment":
            desc = p.get("description") or p.get("item") or raw
            amt = p.get("amount")
            if not amt:
                m = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)', raw, re.IGNORECASE)
                if m:
                    amt = int(float(m.group(1)) * 100)
                else:
                    amt = 99900
            elif isinstance(amt, (int, float)) and amt < 10000 and amt > 0:
                amt = int(amt * 100)
            
            merchant = p.get("merchant_name") or p.get("merchant") or "HELIOS Store"
            curr = p.get("currency", "INR")
            
            prep_res = self.payments.execute_tool_call("prepare_payment", {
                "description": desc,
                "amount": int(amt),
                "currency": curr,
                "merchant_name": merchant,
                "merchant_reference": f"ref_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            })
            
            import json
            return "PAYMENT_INTENT_JSON:" + json.dumps(prep_res)

        # ── GENERAL CHAT (knowledge / conversation fallback) ──────────────────
        if action == "general_chat":
            resp = self.llm.chat(
                prompt=self._chat_prompt(p.get("message", raw)),
                system=self._get_system_prompt())
            content = resp.content
            self.last_used_model = resp.model
            if any(kw in raw.lower() for kw in
                   ("mail", "email", "letter", "compose", "write to", "draft")):
                self._last_draft = content
            return f"{content}\n(via {resp.model})"

    def _get_system_prompt(self) -> str:
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p")
        return (
            f"You are HELIOS, an autonomous desktop AI assistant.\n"
            f"CRITICAL REAL-TIME SYSTEM CONTEXT:\n"
            f"TODAY'S EXACT DATE IS: {date_str}.\n"
            f"CURRENT REAL-TIME SYSTEM TIME IS: {time_str}.\n\n"
            f"Be concise, helpful, and friendly.\n"
            f"For knowledge questions (recipes, how-to, history, science) give a clear\n"
            f"structured answer then offer ONE helpful follow-up action.\n"
            f"Never say you cannot do something you are actually capable of.\n\n"
            f"CRITICAL: You CANNOT perform browser automation, click web elements, fill out forms, login to websites, or add items to carts in real-time."
        )

    # ═════════════════════════════════════════════════════════════════════
    # FILE HELPERS
    # ═════════════════════════════════════════════════════════════════════
    def _list_folder(self, location: str) -> str:
        try:
            from modules.desktop_agent import _safe_iterdir
            folder = LOCATIONS.get(location.lower().strip())
            if folder is None:
                folder = Path(location)
            if not folder.exists():
                return f"Folder '{location}' not found."
            if not folder.is_dir():
                return f"'{location}' is not a folder."

            items = []
            for child in _safe_iterdir(folder):
                try:
                    if child.is_file():
                        sz = child.stat().st_size
                        sz_str = (f"{sz} B" if sz < 1024 else
                                  f"{sz//1024} KB" if sz < 1024**2 else
                                  f"{sz//(1024**2)} MB")
                        items.append((child.name, sz_str))
                except Exception:
                    pass
            items.sort(key=lambda x: x[0].lower())
            if not items:
                return f"No files in {folder}."
            lines = [f"Files in {folder} ({len(items)} total):\n"]
            for name, sz in items[:40]:
                lines.append(f"  • {name}  [{sz}]")
            if len(items) > 40:
                lines.append(f"  … and {len(items)-40} more")
            return "\n".join(lines)
        except Exception as exc:
            log.error("_list_folder error: %s", exc, exc_info=True)
            return f"Error listing folder: {exc}"

    def _search_in_file(self, filename: str, keyword: str) -> str:
        try:
            if not filename:
                return "Please specify a filename."
            if not keyword:
                return "Please specify a keyword to search for."
            if Path(filename).exists():
                return self.desktop.search_in_file(filename, keyword)
            matches = self.desktop.search_file(filename)
            if not matches:
                return f"File '{filename}' not found."
            exact = [m for m in matches
                     if Path(m).name.lower() == filename.lower()]
            candidates = exact if exact else matches
            if len(candidates) == 1:
                return self.desktop.search_in_file(candidates[0], keyword)
            return self._ask_disambig(candidates, "search_in", keyword)
        except Exception as exc:
            log.error("_search_in_file error: %s", exc, exc_info=True)
            return f"Error: {exc}"

    def _move_file(self, name: str, from_loc: str, to_loc: str) -> str:
        try:
            if not name:
                return "Please specify the filename."
            
            # Filename validation against Windows invalid characters
            safe_name = os.path.basename(name).strip()
            if not safe_name or safe_name in (".", ".."):
                return "Invalid filename: Filename cannot be empty, '.', or '..'"
            invalid_chars = set('<>:"/\\|?*')
            found_invalid = [c for c in safe_name if c in invalid_chars]
            if found_invalid:
                return f"Invalid filename: Contains prohibited Windows characters: {', '.join(found_invalid)}"

            dst_dir = LOCATIONS.get(to_loc.lower()) if to_loc else None
            if dst_dir is None:
                return (f"Unknown destination '{to_loc}'.\n"
                        f"Use: desktop, documents, downloads, pictures, music, videos.")

            src_path = None
            if from_loc:
                src_dir = LOCATIONS.get(from_loc.lower())
                if src_dir and (src_dir / safe_name).exists():
                    src_path = src_dir / safe_name

            if src_path is None:
                for folder in [Path.home() / f for f in
                               ("Downloads", "Desktop", "Documents",
                                "Music", "Pictures", "Videos")]:
                    if (folder / safe_name).exists():
                        src_path = folder / safe_name
                        break

            if src_path is None:
                results = self.desktop.search_file(safe_name)
                exact = [r for r in results
                         if Path(r).name.lower() == safe_name.lower()
                         and not any(s in r.lower() for s in
                                     ("program files", "windows", "system32",
                                      "programdata", "appdata"))]
                if not exact:
                    return f"File '{safe_name}' not found."
                if len(exact) > 1:
                    return self._ask_disambig(exact, "move")
                src_path = Path(exact[0])

            # Strong Path Validation & Containment Check
            src_path_abs = Path(src_path).resolve()
            dst_dir_abs = Path(dst_dir).resolve()
            dst_path_abs = (dst_dir_abs / src_path_abs.name).resolve()
            home_dir = Path.home().resolve()

            if not _is_contained(src_path_abs, home_dir) or not _is_contained(dst_path_abs, home_dir):
                log.warning("Security Block: File move operation escaped home directory. Src: %s, Dst: %s", src_path_abs, dst_path_abs)
                return "Security Error: File operations are restricted to your user profile directory."

            dst_dir_abs.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path_abs), str(dst_path_abs))
            log.info("Moved %s → %s", src_path_abs, dst_path_abs)
            return (f"Moved: {src_path_abs.name}\n"
                    f"  From: {src_path_abs.parent}\n"
                    f"  To:   {dst_path_abs.parent}")
        except PermissionError:
            return f"Permission denied moving '{name}'."
        except Exception as exc:
            log.error("_move_file error: %s", exc, exc_info=True)
            return f"Move failed: {exc}"

    def _delete_file(self, path: str, name: str) -> str:
        try:
            target = Path(path) if path else None
            
            # Filename validation if name is specified
            if name:
                safe_name = os.path.basename(name).strip()
                if not safe_name or safe_name in (".", ".."):
                    return "Invalid filename: Filename cannot be empty, '.', or '..'"
                invalid_chars = set('<>:"/\\|?*')
                found_invalid = [c for c in safe_name if c in invalid_chars]
                if found_invalid:
                    return f"Invalid filename: Contains prohibited Windows characters: {', '.join(found_invalid)}"
            else:
                safe_name = ""

            if target is None and safe_name:
                results = self.desktop.search_file(safe_name)
                exact = [r for r in results
                         if Path(r).name.lower() == safe_name.lower()]
                if not exact:
                    return f"File '{safe_name}' not found."
                if len(exact) > 1:
                    return self._ask_disambig(exact, "open")
                target = Path(exact[0])

            if target is None:
                return "Please specify the file."

            # Strong Path Validation & Containment Check
            target_abs = Path(target).resolve()
            home_dir = Path.home().resolve()

            if not _is_contained(target_abs, home_dir):
                log.warning("Security Block: delete_file attempted outside home directory: %s", target_abs)
                return "Security Error: Deleting files outside of your user profile directory is restricted."

            target_abs.unlink()
            log.info("Deleted: %s", target_abs)
            return f"Deleted: {target_abs}"
        except Exception as exc:
            log.error("_delete_file error: %s", exc, exc_info=True)
            return f"Delete failed: {exc}"

    # ═════════════════════════════════════════════════════════════════════
    # SYSTEM INFO
    # ═════════════════════════════════════════════════════════════════════
    def _system_info(self) -> str:
        try:
            cpu  = psutil.cpu_percent(interval=1)
            mem  = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            s    = self.llm.status()

            win_ver = cpu_name = serial = "Unknown"
            try:
                _, o, _ = _ps(
                    "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT"
                    "\\CurrentVersion' | Select-Object ProductName,CurrentBuild,"
                    "DisplayVersion | Format-List | Out-String).Trim()")
                if o: win_ver = o
            except Exception: pass
            try:
                _, o, _ = _ps("(Get-WmiObject -Class Win32_BIOS).SerialNumber")
                if o.strip(): serial = o.strip()
            except Exception: pass
            try:
                _, o, _ = _ps("(Get-WmiObject -Class Win32_Processor).Name")
                if o.strip(): cpu_name = o.strip()
            except Exception: pass

            return (
                f"System Info:\n"
                f"  CPU:      {cpu_name}\n"
                f"  CPU Load: {cpu}%\n"
                f"  RAM:      {mem.used//(1024**2)}MB / "
                f"{mem.total//(1024**2)}MB ({mem.percent}%)\n"
                f"  C: Drive: {disk.used//(1024**3)}GB / "
                f"{disk.total//(1024**3)}GB ({disk.percent}%)\n"
                f"\nWindows:\n  {win_ver}\n"
                f"\nHardware:\n  Serial: {serial}\n"
                f"\nHELIOS:\n"
                f"  Mode:   {s['mode']}\n"
                f"  Ollama: {'online' if s['ollama_alive'] else 'offline'}\n"
                f"  Model:  {s['local_model']}\n"
                f"  Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as exc:
            return f"System info error: {exc}"

    # ═════════════════════════════════════════════════════════════════════
    # OLLAMA
    # ═════════════════════════════════════════════════════════════════════
    def _ollama_pull(self, model: str) -> str:
        if not model: return "Specify a model name — e.g. 'pull gemma3'."
        try:
            r = subprocess.run(["ollama", "pull", model],
                               capture_output=True, text=True, timeout=300)
            return (f"Model '{model}' pulled."
                    if r.returncode == 0 else f"Failed: {r.stderr or r.stdout}")
        except FileNotFoundError:
            return "Ollama not found in PATH."
        except subprocess.TimeoutExpired:
            return f"Timed out — run 'ollama pull {model}' in terminal."

    def _ollama_delete(self, model: str) -> str:
        if not model: return "Specify a model name."
        try:
            r = subprocess.run(["ollama", "rm", model],
                               capture_output=True, text=True, timeout=30)
            return (f"Model '{model}' deleted."
                    if r.returncode == 0 else f"Failed: {r.stderr or r.stdout}")
        except FileNotFoundError:
            return "Ollama not found in PATH."

    def _ollama_list(self) -> str:
        try:
            r = subprocess.run(["ollama", "list"],
                               capture_output=True, text=True, timeout=10)
            return (f"Installed models:\n{r.stdout}"
                    if r.returncode == 0 else f"Error: {r.stderr}")
        except FileNotFoundError:
            return "Ollama not found in PATH."

    # ── Graceful shutdown ─────────────────────────────────────────────────────
    def shutdown(self):
        if getattr(self, "_shutdown_done", False):
            return
        self._shutdown_done = True
        try:
            self.scheduler.shutdown()
            log.info("HELIOS shutdown complete.")
        except Exception as exc:
            log.warning("Scheduler shutdown error: %s", exc)