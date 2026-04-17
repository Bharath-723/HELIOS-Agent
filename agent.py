"""
HELIOS - Agent Orchestrator  v3
Fixes in this version:
  1. Reminders fire INTO the chat window via scheduler callback
  2. File search uses safe traversal (no CrossDevice/junction errors)
  3. list_folder: "list files from downloads" works
  4. search_in_file: "search for word X in file.txt" works
  5. Movie ticket booking wizard (BookMyShow / Paytm Movies)
  6. Disambiguation: multiple file matches ask user to confirm which one
"""

import os
import shutil
import subprocess
import webbrowser
import urllib.parse
import psutil
from datetime import datetime
from pathlib import Path
from core.llm_engine import HybridLLM
from core.nl_router import NLRouter
from modules.desktop_agent import DesktopAgent, WEBSITES
from modules.system_controls import SystemControls
from modules.file_creator import FileCreator
from modules.gmail_composer import GmailComposer
from modules.notes_manager import NotesManager
from modules.task_scheduler import TaskScheduler
from modules.web_search import WebSearch
from modules.chat_history import ChatHistory

HELIOS_CHAT = """You are HELIOS, an autonomous desktop AI assistant.
Be concise, helpful, and friendly. When answering knowledge questions (recipes,
how-to, explanations), give a clear structured answer then offer ONE helpful
follow-up action like opening YouTube or searching the web.
Never say you cannot do things you are capable of as a desktop agent.
"""

DANGEROUS_ACTIONS = {"shutdown", "restart", "empty_recycle", "kill_app"}

LOCATIONS = {
    "desktop":   Path.home() / "Desktop",
    "documents": Path.home() / "Documents",
    "downloads": Path.home() / "Downloads",
    "home":      Path.home(),
    "music":     Path.home() / "Music",
    "pictures":  Path.home() / "Pictures",
    "videos":    Path.home() / "Videos",
}

FOOD_PLATFORMS = {
    "swiggy": "https://www.swiggy.com/search?query={}",
    "zomato": "https://www.zomato.com/search?q={}",
}

MOVIE_PLATFORMS = {
    "bookmyshow": "https://in.bookmyshow.com/explore/movies-{}",
    "paytm":      "https://movies.paytm.com/movies?q={}",
}


def _ps(cmd: str, timeout: int = 20) -> tuple:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


class HELIOSAgent:
    def __init__(self):
        print("[HELIOS] Initializing...")
        self.llm       = HybridLLM()
        self.router    = NLRouter(self.llm)
        self.desktop   = DesktopAgent()
        self.sysctrl   = SystemControls()
        self.files     = FileCreator()
        self.gmail     = GmailComposer()
        self.notes     = NotesManager(self.llm)
        self.scheduler = TaskScheduler()          # callback set after init
        self.search    = WebSearch(self.llm)
        self.history   = ChatHistory()

        # Flow / confirmation state
        self._pending_action  = None
        self._pending_params  = None
        self._pending_raw     = None
        self._flow            = None
        self._flow_data       = {}
        self._last_draft      = ""
        # Disambiguation state: list of candidate file paths waiting for user pick
        self._disambig_items  = []
        self._disambig_action = None   # "play" | "open" | "search_in"
        self._disambig_kw     = ""     # keyword for search_in_file

        # Wire reminder notifications back into the chat window
        self._ui_notify_cb    = None   # set by popup after init
        self.scheduler.set_notify_callback(self._on_reminder)

        print("[HELIOS] Ready.")

    def set_ui_notify(self, cb):
        """Called by helios_popup to wire reminders into the chat window."""
        self._ui_notify_cb = cb

    def _on_reminder(self, msg: str):
        """Called by scheduler when a reminder fires."""
        self.history.add("helios", msg)
        if self._ui_notify_cb:
            try:
                self._ui_notify_cb(msg)
            except Exception:
                pass

    # ═════════════════════════════════════════════════════════════════════
    # PUBLIC ENTRY POINT
    # ═════════════════════════════════════════════════════════════════════
    def process(self, user_input: str) -> str:
        if not user_input.strip():
            return "Please enter a command."

        self.history.add("user", user_input)

        # 1. Disambiguation choice pending
        if self._disambig_items:
            result = self._handle_disambig(user_input)
            self.history.add("helios", result)
            return result

        # 2. Dangerous confirmation pending
        if self._pending_action:
            result = self._handle_confirmation(user_input)
            self.history.add("helios", result)
            return result

        # 3. Multi-step flow active
        if self._flow:
            result = self._continue_flow(user_input)
            self.history.add("helios", result)
            return result

        # 4. Normal routing
        parsed = self.router.parse(user_input, self._get_context())
        action = parsed.get("action", "general_chat")
        p      = parsed.get("params", {})

        if action in DANGEROUS_ACTIONS:
            self._pending_action = action
            self._pending_params = p
            self._pending_raw    = user_input
            msg = self._confirmation_prompt(action, p)
            self.history.add("helios", msg)
            return msg

        result = self._execute(action, p, user_input)
        self.history.add("helios", result)
        return result

    # ═════════════════════════════════════════════════════════════════════
    # CONTEXT
    # ═════════════════════════════════════════════════════════════════════
    def _get_context(self) -> str:
        msgs = self.history.messages[-6:] if self.history.messages else []
        lines = []
        for m in msgs:
            role = "User" if m["role"] == "user" else "HELIOS"
            lines.append(f"{role}: {m['content'][:300]}")
        return "\n".join(lines)

    def _chat_prompt(self, message: str) -> str:
        ctx = self._get_context()
        if ctx:
            return f"Conversation so far:\n{ctx}\n\nUser: {message}"
        return message

    # ═════════════════════════════════════════════════════════════════════
    # DISAMBIGUATION
    # ═════════════════════════════════════════════════════════════════════
    def _ask_disambig(self, items: list, action: str, keyword: str = "") -> str:
        """Store candidates and ask user to pick one."""
        self._disambig_items  = items
        self._disambig_action = action
        self._disambig_kw     = keyword
        lines = [f"Found {len(items)} matching files. Which one do you mean?\n"]
        for i, path in enumerate(items[:8], 1):
            lines.append(f"  {i}. {Path(path).name}  ({Path(path).parent})")
        lines.append("\nReply with the number (e.g. '2') or part of the name.")
        return "\n".join(lines)

    def _handle_disambig(self, user_input: str) -> str:
        items  = self._disambig_items
        action = self._disambig_action
        kw     = self._disambig_kw
        inp    = user_input.strip()

        # Clear state
        self._disambig_items  = []
        self._disambig_action = None
        self._disambig_kw     = ""

        # Try numeric pick
        if inp.isdigit():
            idx = int(inp) - 1
            if 0 <= idx < len(items):
                chosen = items[idx]
            else:
                return f"Invalid choice. Please try again."
        else:
            # Match by name fragment
            matches = [p for p in items if inp.lower() in Path(p).name.lower()]
            if len(matches) == 1:
                chosen = matches[0]
            elif len(matches) == 0:
                return f"No match for '{inp}'. Cancelled."
            else:
                # Still ambiguous — re-ask with filtered list
                return self._ask_disambig(matches, action, kw)

        # Execute the chosen action
        if action == "play":
            try:
                os.startfile(chosen)
                return f"Playing: {Path(chosen).name}\nPath: {chosen}"
            except Exception as e:
                return f"Could not open '{Path(chosen).name}': {e}"
        elif action == "open":
            try:
                os.startfile(chosen)
                return f"Opened: {Path(chosen).name}"
            except Exception as e:
                return f"Could not open '{Path(chosen).name}': {e}"
        elif action == "search_in":
            return self.desktop.search_in_file(chosen, kw)
        else:
            try:
                os.startfile(chosen)
                return f"Opened: {Path(chosen).name}"
            except Exception as e:
                return f"Error: {e}"

    # ═════════════════════════════════════════════════════════════════════
    # CONFIRMATION
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

    def _handle_confirmation(self, user_input: str) -> str:
        yes = {"yes", "y", "yeah", "yep", "ok", "okay", "sure", "confirm", "do it", "proceed"}
        no  = {"no", "n", "nope", "cancel", "stop", "abort"}
        inp = user_input.lower().strip()

        action = self._pending_action
        p      = self._pending_params
        raw    = self._pending_raw
        self._pending_action = self._pending_params = self._pending_raw = None

        if any(w in inp for w in yes):
            return self._execute(action, p, raw)
        if any(w in inp for w in no):
            return f"Cancelled — '{action}' was not executed."
        self._pending_action = action
        self._pending_params = p
        self._pending_raw    = raw
        return "Please reply 'yes' to confirm or 'no' to cancel."

    # ═════════════════════════════════════════════════════════════════════
    # MULTI-STEP FLOW ENGINE
    # ═════════════════════════════════════════════════════════════════════
    def _continue_flow(self, user_input: str) -> str:
        if self._flow == "order_food":
            return self._food_flow_step(user_input)
        if self._flow == "book_movie":
            return self._movie_flow_step(user_input)
        self._flow = None
        self._flow_data = {}
        return self.process(user_input)

    # ── Food ordering ──────────────────────────────────────────────────
    def _start_food_flow(self, item, platform, location, budget) -> str:
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
                d["platform"] = "swiggy" if "swiggy" in r else \
                                "zomato" if "zomato" in r else r
            elif not d["location"]:
                d["location"] = reply.strip()
            elif not d["budget"]:
                d["budget"] = reply.strip() if any(c.isdigit() for c in reply) else "any"

        if not d["platform"]:
            return (f"Sure! Where should I order {d['item'] or 'food'} from?\n"
                    f"Reply: Swiggy or Zomato")
        if not d["location"]:
            return f"Got it — {d['platform'].title()}. What's your delivery location?"
        if not d["budget"]:
            return "What's your budget? (e.g. 200, 500, or 'any')"

        item     = d["item"] or "food"
        platform = d["platform"]
        url_tmpl = FOOD_PLATFORMS.get(platform,
                                      f"https://www.{platform}.com/search?q={{}}")
        url = url_tmpl.format(urllib.parse.quote(item))
        webbrowser.open(url)
        self._flow = None
        self._flow_data = {}
        return (f"Opening {platform.title()} to order: {item}\n"
                f"  Location: {d['location']}\n"
                f"  Budget:   {d['budget']}\n\n"
                f"{platform.title()} search results are now open in your browser.\n"
                f"Select a restaurant, add to cart, and place your order!")

    # ── Movie ticket booking ───────────────────────────────────────────
    def _start_movie_flow(self, movie, platform, city, date) -> str:
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
                d["platform"] = "bookmyshow" if "bms" in r or "bookmyshow" in r else \
                                "paytm"       if "paytm" in r else \
                                "bookmyshow"  # default
            elif not d["city"]:
                d["city"] = reply.strip()
            elif not d["date"]:
                d["date"] = reply.strip() if reply.strip().lower() != "today" \
                            else datetime.now().strftime("%d %b %Y")

        if not d["platform"]:
            return ("Which platform to book on?\n"
                    "  1. BookMyShow\n"
                    "  2. Paytm Movies\n"
                    "Reply with the name or number.")

        if not d["city"]:
            return (f"Got it — {d['platform'].title()}.\n"
                    f"Which city are you in? (e.g. Hyderabad, Mumbai, Bangalore)")

        if not d["date"]:
            return ("Which date? (e.g. today, tomorrow, 20 Apr)\n"
                    "Or type 'any' to see all shows.")

        return self._open_movie_booking()

    def _open_movie_booking(self) -> str:
        d        = self._flow_data
        movie    = d.get("movie", "")
        platform = d.get("platform", "bookmyshow")
        city     = d.get("city", "")
        date     = d.get("date", "")

        city_slug = city.lower().replace(" ", "-")
        movie_enc = urllib.parse.quote(movie)

        if platform == "bookmyshow":
            if city_slug:
                url = f"https://in.bookmyshow.com/explore/movies-{city_slug}"
            else:
                url = f"https://in.bookmyshow.com/explore/movies"
            # If movie name given, append search
            if movie:
                url = (f"https://in.bookmyshow.com/search?"
                       f"q={movie_enc}&geoId=HYBD")
        else:  # paytm
            url = f"https://movies.paytm.com/movies?q={movie_enc}"

        webbrowser.open(url)
        self._flow = None
        self._flow_data = {}

        return (f"Opening {platform.title()} for movie tickets:\n"
                f"  Movie:    {movie or 'browsing all'}\n"
                f"  City:     {city}\n"
                f"  Date:     {date}\n\n"
                f"Ticket booking page is open in your browser.\n"
                f"Select your theatre, showtime, and seats!")

    # ═════════════════════════════════════════════════════════════════════
    # EXECUTE
    # ═════════════════════════════════════════════════════════════════════
    def _execute(self, action: str, p: dict, raw: str) -> str:

        # ── MEDIA ────────────────────────────────────────────────────────
        if action == "play_media":
            query   = p.get("query", raw)
            matches = self.desktop.play_media(query)
            if isinstance(matches, str):
                return matches          # error message
            if len(matches) == 0:
                return f"No media file found matching '{query}'."
            if len(matches) == 1:
                try:
                    os.startfile(matches[0])
                    return f"Playing: {Path(matches[0]).name}\nPath: {matches[0]}"
                except Exception as e:
                    return f"Could not play: {e}"
            # Multiple matches — disambiguate
            return self._ask_disambig(matches, "play")

        # ── APPS ─────────────────────────────────────────────────────────
        if action == "open_app":
            app   = p.get("app", raw)
            query = p.get("query", "") or p.get("search", "")
            if query and "explorer" in app.lower():
                return self.desktop.open_explorer_search(query)
            return self.desktop.open_app(app)
        if action == "kill_app":
            return self.desktop.kill_app(p.get("app", raw))
        if action == "open_website":
            return self.desktop.open_website(p.get("site", ""))
        if action == "open_url":
            return self.desktop.open_url(p.get("url", ""))
        if action == "search_google":
            return self.desktop.search_google(p.get("query", raw))
        if action == "search_youtube":
            return self.desktop.search_youtube(p.get("query", raw))
        if action == "open_explorer_search":
            return self.desktop.open_explorer_search(p.get("query", raw))

        # ── FOOD ORDERING ────────────────────────────────────────────────
        if action == "order_food":
            return self._start_food_flow(
                p.get("item", ""), p.get("platform", ""),
                p.get("location", ""), p.get("budget", ""))

        # ── MOVIE BOOKING ────────────────────────────────────────────────
        if action == "book_movie":
            return self._start_movie_flow(
                p.get("movie", ""), p.get("platform", ""),
                p.get("city", ""), p.get("date", ""))

        # ── FILES ────────────────────────────────────────────────────────
        if action == "create_file":
            return self.files.create_file(
                name=p.get("name", "helios_file.txt"),
                location=p.get("location", "desktop"),
                content=p.get("content", ""))

        if action == "list_folder":
            location = p.get("location", p.get("query", raw))
            return self._list_folder(location)

        if action == "find_file":
            query   = p.get("query", raw)
            folders = self.desktop.search_folder(query)
            files   = self.desktop.search_file(query)
            results = folders + [f for f in files if f not in folders]
            if not results:
                return f"No files or folders found matching '{query}'."
            return (f"Found {len(results)} result(s):\n" +
                    "\n".join(f"  • {r}" for r in results[:15]))

        if action == "open_file":
            path = p.get("path", "")
            if path and Path(path).exists():
                try:
                    os.startfile(path)
                    return f"Opened: {Path(path).name}"
                except Exception as e:
                    return f"Could not open: {e}"
            return f"File not found: {path}"

        if action == "search_in_file":
            filename = p.get("filename", p.get("file", ""))
            keyword  = p.get("keyword", p.get("word", ""))
            if not keyword:
                return "Please specify a keyword to search for."
            return self._search_in_file(filename, keyword)

        if action == "move_file":
            return self._move_file(
                name=p.get("name", ""),
                from_loc=p.get("from", ""),
                to_loc=p.get("to", ""))
        if action == "delete_file":
            return self._delete_file(p.get("path", ""), p.get("name", ""))

        # ── EMAIL ────────────────────────────────────────────────────────
        if action == "compose_gmail":
            body = p.get("body", "")
            if not body and self._last_draft:
                body = self._last_draft
            result = self.gmail.compose(
                to=p.get("to", ""),
                subject=p.get("subject", ""),
                body=body)
            self._last_draft = ""
            return result
        if action == "open_gmail":
            return self.gmail.open_gmail()

        # ── WIFI ─────────────────────────────────────────────────────────
        if action == "wifi_on":     return self.sysctrl.wifi_on()
        if action == "wifi_off":    return self.sysctrl.wifi_off()
        if action == "wifi_status": return self.sysctrl.wifi_status()

        # ── BLUETOOTH ────────────────────────────────────────────────────
        if action == "bluetooth_on":  return self.sysctrl.bluetooth_on()
        if action == "bluetooth_off": return self.sysctrl.bluetooth_off()

        # ── AIRPLANE ─────────────────────────────────────────────────────
        if action == "airplane_mode_on":  return self.sysctrl.airplane_mode_on()
        if action == "airplane_mode_off": return self.sysctrl.airplane_mode_off()

        # ── BRIGHTNESS ───────────────────────────────────────────────────
        if action == "brightness_set":
            return self.sysctrl.set_brightness(int(p.get("level", 70)))
        if action == "brightness_up":
            return self.sysctrl.brightness_up(int(p.get("amount", 10)))
        if action == "brightness_down":
            return self.sysctrl.brightness_down(int(p.get("amount", 10)))

        # ── VOLUME ───────────────────────────────────────────────────────
        if action == "volume_up":   return self.desktop.volume_up(int(p.get("steps", 5)))
        if action == "volume_down": return self.desktop.volume_down(int(p.get("steps", 5)))
        if action == "mute":        return self.desktop.mute()

        # ── SYSTEM ───────────────────────────────────────────────────────
        if action == "screenshot":        return self.desktop.screenshot()
        if action == "lock_screen":       return self.desktop.lock_screen()
        if action == "shutdown":          return self.desktop.shutdown(int(p.get("delay", 0)))
        if action == "restart":           return self.desktop.restart()
        if action == "sleep":             return self.desktop.sleep()
        if action == "battery":           return self.desktop.battery_status()
        if action == "disk_space":        return self.desktop.disk_space()
        if action == "system_info":       return self._system_info()
        if action == "running_apps":      return self.desktop.running_apps()
        if action == "ip_address":        return self.desktop.ip_address()
        if action == "empty_recycle":     return self.desktop.empty_recycle()
        if action == "dark_mode_on":      return self.sysctrl.dark_mode_on()
        if action == "dark_mode_off":     return self.sysctrl.dark_mode_off()
        if action == "power_performance": return self.sysctrl.power_performance()
        if action == "power_balanced":    return self.sysctrl.power_balanced()
        if action == "power_saver":       return self.sysctrl.power_saver()
        if action == "flush_dns":         return self.sysctrl.flush_dns()
        if action == "open_settings":     return self.sysctrl.open_settings(p.get("page", ""))
        if action == "open_task_manager": return self.sysctrl.open_task_manager()
        if action == "top_processes":     return self.sysctrl.top_processes()

        # ── OLLAMA ───────────────────────────────────────────────────────
        if action == "ollama_pull":   return self._ollama_pull(p.get("model", ""))
        if action == "ollama_delete": return self._ollama_delete(p.get("model", ""))
        if action == "ollama_list":   return self._ollama_list()

        # ── NOTES ────────────────────────────────────────────────────────
        if action == "create_note":
            return self.notes.create(p.get("title", "Untitled"), p.get("content", ""))
        if action == "list_notes":   return self.notes.list_notes()
        if action == "read_note":    return self.notes.read(p.get("title", ""))
        if action == "search_notes": return self.notes.search(p.get("query", raw))

        # ── TASKS ────────────────────────────────────────────────────────
        if action == "schedule_task":
            return self.scheduler.schedule(
                p.get("description", raw), p.get("time", "in 1 hour"))
        if action == "list_tasks":  return self.scheduler.list_tasks()
        if action == "cancel_task": return self.scheduler.cancel_task(p.get("id", ""))

        # ── WEB SEARCH ───────────────────────────────────────────────────
        if action == "web_search":
            return self.search.search(p.get("query", raw))

        # ── GENERAL CHAT ─────────────────────────────────────────────────
        resp = self.llm.chat(
            prompt=self._chat_prompt(p.get("message", raw)),
            system=HELIOS_CHAT)
        content = resp.content
        if any(kw in raw.lower() for kw in
               ["mail", "email", "letter", "compose", "write to", "draft"]):
            self._last_draft = content
        return f"{content}\n(via {resp.model})"

    # ═════════════════════════════════════════════════════════════════════
    # FILE HELPERS
    # ═════════════════════════════════════════════════════════════════════
    def _list_folder(self, location: str) -> str:
        """List files in a known folder or path."""
        # Resolve location name → Path
        folder = LOCATIONS.get(location.lower().strip())
        if folder is None:
            # Try treating as a raw path
            folder = Path(location)
        if not folder.exists():
            return f"Folder '{location}' not found."
        if not folder.is_dir():
            return f"'{location}' is not a folder."

        from modules.desktop_agent import _safe_iterdir
        items = []
        for child in _safe_iterdir(folder):
            try:
                if child.is_file(follow_symlinks=False):
                    size = child.stat().st_size
                    if size < 1024:
                        sz = f"{size} B"
                    elif size < 1024 * 1024:
                        sz = f"{size // 1024} KB"
                    else:
                        sz = f"{size // (1024*1024)} MB"
                    items.append((child.name, sz))
            except Exception:
                pass
        items.sort(key=lambda x: x[0].lower())

        if not items:
            return f"No files found in {folder}."

        lines = [f"Files in {folder} ({len(items)} total):\n"]
        for name, sz in items[:40]:
            lines.append(f"  • {name}  [{sz}]")
        if len(items) > 40:
            lines.append(f"  ... and {len(items)-40} more files")
        return "\n".join(lines)

    def _search_in_file(self, filename: str, keyword: str) -> str:
        """Find a file by name then search for a keyword inside it."""
        if not filename:
            return "Please specify a filename to search in."

        # Try exact path first
        if Path(filename).exists():
            return self.desktop.search_in_file(filename, keyword)

        # Search for the file
        matches = self.desktop.search_file(filename)
        if not matches:
            return f"File '{filename}' not found in your user folders."

        # Filter to exact or close name match
        exact = [m for m in matches
                 if Path(m).name.lower() == filename.lower()]
        candidates = exact if exact else matches

        if len(candidates) == 1:
            return self.desktop.search_in_file(candidates[0], keyword)

        # Multiple files — ask user
        return self._ask_disambig(candidates, "search_in", keyword)

    def _move_file(self, name: str, from_loc: str, to_loc: str) -> str:
        if not name:
            return "Please specify the file name to move."
        dst_dir = LOCATIONS.get(to_loc.lower()) if to_loc else None
        if dst_dir is None:
            return (f"Unknown destination '{to_loc}'.\n"
                    f"Use: desktop, documents, downloads, pictures, music, videos.")

        src_path = None
        if from_loc:
            src_dir = LOCATIONS.get(from_loc.lower())
            if src_dir:
                candidate = src_dir / name
                if candidate.exists():
                    src_path = candidate

        if src_path is None:
            for folder in [Path.home() / f for f in
                           ["Downloads", "Desktop", "Documents",
                            "Music", "Pictures", "Videos"]]:
                c = folder / name
                if c.exists():
                    src_path = c
                    break

        if src_path is None:
            results = self.desktop.search_file(name)
            exact = [r for r in results
                     if Path(r).name.lower() == name.lower()
                     and not any(s in r.lower() for s in
                                 ["program files", "windows", "system32",
                                  "programdata", "appdata"])]
            if not exact:
                return (f"File '{name}' not found.\n"
                        f"Check the filename is exact (including extension).")
            if len(exact) > 1:
                return self._ask_disambig(exact, "move")
            src_path = Path(exact[0])

        dst_dir.mkdir(parents=True, exist_ok=True)
        dst_path = dst_dir / src_path.name
        try:
            shutil.move(str(src_path), str(dst_path))
            return (f"Moved: {src_path.name}\n"
                    f"  From: {src_path.parent}\n"
                    f"  To:   {dst_path.parent}")
        except PermissionError:
            return f"Permission denied moving '{src_path.name}'."
        except Exception as e:
            return f"Failed to move: {e}"

    def _delete_file(self, path: str, name: str) -> str:
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
            return "Please specify the file to delete."
        try:
            target.unlink()
            return f"Deleted: {target}"
        except Exception as e:
            return f"Could not delete: {e}"

    # ═════════════════════════════════════════════════════════════════════
    # SYSTEM INFO
    # ═════════════════════════════════════════════════════════════════════
    def _system_info(self) -> str:
        cpu  = psutil.cpu_percent(interval=1)
        mem  = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        s    = self.llm.status()

        win_ver = serial = cpu_name = "Unknown"
        try:
            c, o, _ = _ps(
                "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'"
                " | Select-Object ProductName,CurrentBuild,DisplayVersion"
                " | Format-List | Out-String).Trim()")
            if o: win_ver = o
        except Exception: pass
        try:
            c, o, _ = _ps("(Get-WmiObject -Class Win32_BIOS).SerialNumber")
            if o.strip(): serial = o.strip()
        except Exception: pass
        try:
            c, o, _ = _ps("(Get-WmiObject -Class Win32_Processor).Name")
            if o.strip(): cpu_name = o.strip()
        except Exception: pass

        return (
            f"System Info:\n"
            f"  CPU:      {cpu_name}\n"
            f"  CPU Load: {cpu}%\n"
            f"  RAM:      {mem.used//(1024**2)}MB / {mem.total//(1024**2)}MB ({mem.percent}%)\n"
            f"  C: Drive: {disk.used//(1024**3)}GB / {disk.total//(1024**3)}GB ({disk.percent}%)\n"
            f"\nWindows:\n  {win_ver}\n"
            f"\nHardware:\n  Serial No: {serial}\n"
            f"\nHELIOS:\n"
            f"  Mode:     {s['mode']}\n"
            f"  Ollama:   {'online' if s['ollama_alive'] else 'offline'}\n"
            f"  Model:    {s['local_model']}\n"
            f"  Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    # ═════════════════════════════════════════════════════════════════════
    # OLLAMA
    # ═════════════════════════════════════════════════════════════════════
    def _ollama_pull(self, model: str) -> str:
        if not model: return "Specify a model name, e.g. 'pull gemma3'."
        try:
            r = subprocess.run(["ollama", "pull", model],
                               capture_output=True, text=True, timeout=300)
            return f"Model '{model}' pulled." if r.returncode == 0 \
                   else f"Failed: {r.stderr or r.stdout}"
        except FileNotFoundError: return "Ollama not found in PATH."
        except subprocess.TimeoutExpired:
            return f"Timed out — run 'ollama pull {model}' in terminal."

    def _ollama_delete(self, model: str) -> str:
        if not model: return "Specify a model name."
        try:
            r = subprocess.run(["ollama", "rm", model],
                               capture_output=True, text=True, timeout=30)
            return f"Model '{model}' deleted." if r.returncode == 0 \
                   else f"Failed: {r.stderr or r.stdout}"
        except FileNotFoundError: return "Ollama not found in PATH."

    def _ollama_list(self) -> str:
        try:
            r = subprocess.run(["ollama", "list"],
                               capture_output=True, text=True, timeout=10)
            return f"Installed models:\n{r.stdout}" if r.returncode == 0 \
                   else f"Error: {r.stderr}"
        except FileNotFoundError: return "Ollama not found in PATH."

    def shutdown(self):
        self.scheduler.shutdown()
