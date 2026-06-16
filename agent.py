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
import logging
import shutil
import subprocess
import webbrowser
import urllib.parse
import psutil
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
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),                            # console
        logging.FileHandler("helios.log", encoding="utf-8"),  # file
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
        self.history   = ChatHistory()

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

        log.info("HELIOS ready.")

    # ── External wiring ───────────────────────────────────────────────────────
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
                self._last_search_results = [] # clear results
                self.history.add("helios", result)
                return result

        # Priority 4: normal routing
        parsed = self.router.parse(text, self._get_context())
        action = parsed.get("action", "general_chat")
        params = parsed.get("params", {}) or {}
        log.info("Routed → action=%s params=%s", action, params)

        if action in DANGEROUS_ACTIONS:
            self._pending_action = action
            self._pending_params = params
            self._pending_raw    = text
            msg = self._confirmation_prompt(action, params)
            self.history.add("helios", msg)
            return msg

        result = self._execute(action, params, text)
        log.info("Result: %s", result[:120].replace("\n", " "))
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
        return f"Conversation:\n{ctx}\n\nUser: {message}" if ctx else message

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
                import re
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

        if action == "find_file":
            query   = p.get("query") or raw
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
            return self._move_file(
                p.get("name", ""), p.get("from", ""), p.get("to", ""))

        if action == "delete_file":
            return self._delete_file(p.get("path", ""), p.get("name", ""))

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
            return self.sysctrl.set_brightness(int(p.get("level", 70)))
        if action == "brightness_up":
            return self.sysctrl.brightness_up(int(p.get("amount", 10)))
        if action == "brightness_down":
            return self.sysctrl.brightness_down(int(p.get("amount", 10)))

        # ── VOLUME ────────────────────────────────────────────────────────────
        if action == "volume_up":
            return self.desktop.volume_up(int(p.get("steps", 5)))
        if action == "volume_down":
            return self.desktop.volume_down(int(p.get("steps", 5)))
        if action == "mute":
            return self.desktop.mute()
        if action == "pause_media":
            return self.desktop.pause_media()
        if action == "stop_media":
            return self.desktop.stop_media()

        # ── SYSTEM ────────────────────────────────────────────────────────────
        if action == "screenshot":         return self.desktop.screenshot()
        if action == "lock_screen":        return self.desktop.lock_screen()
        if action == "shutdown":           return self.desktop.shutdown(int(p.get("delay", 0)))
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

        # ── GENERAL CHAT (knowledge / conversation fallback) ──────────────────
        resp    = self.llm.chat(
            prompt=self._chat_prompt(p.get("message", raw)),
            system=HELIOS_CHAT)
        content = resp.content
        # Store as draft if it looks like an email was composed
        if any(kw in raw.lower() for kw in
               ("mail", "email", "letter", "compose", "write to", "draft")):
            self._last_draft = content
        return f"{content}\n(via {resp.model})"

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
            dst_dir = LOCATIONS.get(to_loc.lower()) if to_loc else None
            if dst_dir is None:
                return (f"Unknown destination '{to_loc}'.\n"
                        f"Use: desktop, documents, downloads, pictures, music, videos.")

            src_path = None
            if from_loc:
                src_dir = LOCATIONS.get(from_loc.lower())
                if src_dir and (src_dir / name).exists():
                    src_path = src_dir / name

            if src_path is None:
                for folder in [Path.home() / f for f in
                               ("Downloads", "Desktop", "Documents",
                                "Music", "Pictures", "Videos")]:
                    if (folder / name).exists():
                        src_path = folder / name
                        break

            if src_path is None:
                results = self.desktop.search_file(name)
                exact = [r for r in results
                         if Path(r).name.lower() == name.lower()
                         and not any(s in r.lower() for s in
                                     ("program files", "windows", "system32",
                                      "programdata", "appdata"))]
                if not exact:
                    return f"File '{name}' not found."
                if len(exact) > 1:
                    return self._ask_disambig(exact, "move")
                src_path = Path(exact[0])

            dst_dir.mkdir(parents=True, exist_ok=True)
            dst_path = dst_dir / src_path.name
            shutil.move(str(src_path), str(dst_path))
            log.info("Moved %s → %s", src_path, dst_path)
            return (f"Moved: {src_path.name}\n"
                    f"  From: {src_path.parent}\n"
                    f"  To:   {dst_path.parent}")
        except PermissionError:
            return f"Permission denied moving '{name}'."
        except Exception as exc:
            log.error("_move_file error: %s", exc, exc_info=True)
            return f"Move failed: {exc}"

    def _delete_file(self, path: str, name: str) -> str:
        try:
            target = Path(path) if path else None
            if target is None and name:
                results = self.desktop.search_file(name)
                exact = [r for r in results
                         if Path(r).name.lower() == name.lower()]
                if not exact:
                    return f"File '{name}' not found."
                if len(exact) > 1:
                    return self._ask_disambig(exact, "open")
                target = Path(exact[0])
            if target is None:
                return "Please specify the file."
            target.unlink()
            log.info("Deleted: %s", target)
            return f"Deleted: {target}"
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
        try:
            self.scheduler.shutdown()
            log.info("HELIOS shutdown complete.")
        except Exception as exc:
            log.warning("Scheduler shutdown error: %s", exc)