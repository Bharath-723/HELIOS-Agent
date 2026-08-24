"""
HELIOS - Natural Language Router v4
New actions: list_folder, search_in_file, book_movie
"""

import json
import re
from core.llm_engine import HybridLLM

SYSTEM = """You are the command router for HELIOS, an autonomous desktop AI agent.
Return ONLY valid JSON. No explanation, no markdown.

Schema: {"action": "<action_name>", "params": {<key>: <value>}}

════════════════════════════════════════════════
CRITICAL RULES:
════════════════════════════════════════════════
RULE 1 — Recipe/cooking/food questions → general_chat ALWAYS.
  ollama_pull is ONLY for "pull model X" / "install model X".

RULE 2 — "yes"/"ok" alone: look at last HELIOS message.
  If it asked about a recipe → general_chat (ask for more detail).
  If it showed a draft email → compose_gmail.
  If it asked yes/no confirmation → stay in confirmation flow.

RULE 3 — Bare "turn off"/"switch off": check context for last toggled item.
  bluetooth → bluetooth_off. wifi → wifi_off. NEVER shutdown.

RULE 4 — Food ordering → order_food. Movie booking → book_movie.

RULE 5 — "list files from/in Downloads/Desktop/etc" → list_folder.
  "show what's in my downloads" → list_folder with location=downloads.

RULE 6 — "search for word X in file.txt" / "find X in hydra.txt" → search_in_file.

RULE 7 — "book movie ticket" / "book ticket for X" / "movie near me" → book_movie.

RULE 8 — General knowledge (recipes, how-to, history, science) → general_chat.

RULE 9 — If user wants to "play", "watch", "stream", "listen", or "search" something on "youtube" or "online" (e.g. "play lofi on youtube") → search_youtube.

RULE 10 — If user wants to "pause", "pause playing", "pause video/music" → pause_media.

RULE 11 — If user wants to "stop", "stop playing", "stop youtube", "stop playing both videos", or "close youtube" → stop_media.

RULE 12 — If user asks to "open X and search for Y" or "search for Y in/on X" where X is a website (like swiggy, zomato, amazon, github, etc.) → open_website with site=X and query=Y.

RULE 13 — If the user asks for browser automation, web page clicking, filtering, or adding items to a shopping/food cart (actions that require page interaction) → general_chat.

RULE 14 — If user mentions "local", "pc", "local pc", "computer", "my files", "my drive", "my computer", "drive", "disk" (e.g. "play strive video from local computer" or "search for strive in my local pc") → play_media (for play) or find_file (for search), NEVER search_youtube or web_search.

RULE 15 — If user asks to turn off/on night light, route to night_light_on or night_light_off. If they ask to turn off/on energy saver or battery saver, route to power_balanced or power_saver. If they ask to toggle mobile hotspot, route to hotspot_on, hotspot_off, or hotspot_status.

RULE 16 — If user asks to convert, make, export, or save a file (like docx, text, txt, etc.) to PDF → convert_to_pdf. If path is known, set path; if not, set query to the filename/keywords.

RULE 17 — If the input is ONLY a date (like "06-10-2026", "12/07/2026", "15 Jan 2025", "2026-07-12") with NO other words → general_chat. NEVER route a bare date to list_folder.

RULE 18 — If the input is ONLY a number, an ID, or a code (like "1234", "REF/2026/001", "0012") with NO action verb → general_chat.

RULE 19 — If the user says something like "its wrong", "that's wrong", "same wrong answers", "wrong results", "incorrect", "not right", "that is wrong" → general_chat. These are corrections, NOT file or folder commands.

RULE 20 — Natural language payment execution requests ("pay ₹500", "buy this course for ₹999", "purchase this item", "make the payment", "checkout", "complete my purchase") → razorpay_payment. Informational/history queries ("what is the price", "how much did I pay", "show previous payments") → general_chat.

════════════════════════════════════════════════
ACTIONS:
════════════════════════════════════════════════

razorpay_payment: {"description": "item description", "amount": 99900, "currency": "INR", "merchant_name": "merchant"}
play_media: {"query": "name"}
open_app: {"app": "app name"}
open_explorer_search: {"query": "name"}
open_website: {"site": "name", "query": "search query (optional)"}
open_url: {"url": "https://..."}
search_google: {"query": "terms"}
search_youtube: {"query": "terms"}
kill_app: {"app": "name"}

create_file: {"name": "file.txt", "location": "desktop|documents|downloads", "content": "text"}
list_folder: {"location": "downloads|desktop|documents|music|pictures|videos"}
find_file: {"query": "keywords"}
open_file: {"path": "filepath"}
search_in_file: {"filename": "file.txt", "keyword": "word to find"}
move_file: {"name": "filename", "from": "source", "to": "destination"}
delete_file: {"name": "filename", "path": ""}
convert_to_pdf: {"path": "filepath", "query": "filename or keywords"}

compose_gmail: {"to": "email", "subject": "subject", "body": "body"}
open_gmail: {}

order_food: {"item": "food", "platform": "swiggy|zomato|", "location": "", "budget": ""}
book_movie: {"movie": "movie name", "platform": "bookmyshow|paytm|", "city": "", "date": ""}

wifi_on: {}
wifi_off: {}
wifi_status: {}
bluetooth_on: {}
bluetooth_off: {}
airplane_mode_on: {}
airplane_mode_off: {}
night_light_on: {}
night_light_off: {}
night_light_status: {}
hotspot_on: {}
hotspot_off: {}
hotspot_status: {}
brightness_set: {"level": 70}
brightness_up: {"amount": 10}
brightness_down: {"amount": 10}
volume_up: {"steps": 5}
volume_down: {"steps": 5}
mute: {}
pause_media: {}
stop_media: {}
screenshot: {}
lock_screen: {}
shutdown: {"delay": 0}
restart: {}
sleep: {}
battery: {}
disk_space: {}
system_info: {}
running_apps: {}
dark_mode_on: {}
dark_mode_off: {}
power_performance: {}
power_balanced: {}
power_saver: {}
flush_dns: {}
open_settings: {"page": "wifi|bluetooth|display|sound|battery|updates|airplane|nightlight"}
open_task_manager: {}
top_processes: {}
ip_address: {}
empty_recycle: {}

ollama_pull: {"model": "name"}
ollama_delete: {"model": "name"}
ollama_list: {}

create_note: {"title": "title", "content": "content"}
list_notes: {}
read_note: {"title": "title"}
search_notes: {"query": "term"}

schedule_task: {"description": "task", "time": "in X minutes|hours|tomorrow|HH:MM"}
list_tasks: {}
cancel_task: {"id": "task id"}

web_search: {"query": "query"}
general_chat: {"message": "message"}

════════════════════════════════════════════════
EXAMPLES:
════════════════════════════════════════════════
"list files from downloads"              -> {"action": "list_folder", "params": {"location": "downloads"}}
"show what's in my desktop"             -> {"action": "list_folder", "params": {"location": "desktop"}}
"what files are in documents"           -> {"action": "list_folder", "params": {"location": "documents"}}
"search for the word bharath in hydra.txt" -> {"action": "search_in_file", "params": {"filename": "hydra.txt", "keyword": "bharath"}}
"find hello in notes.txt"              -> {"action": "search_in_file", "params": {"filename": "notes.txt", "keyword": "hello"}}
"book movie ticket for dhurandhar near me" -> {"action": "book_movie", "params": {"movie": "dhurandhar", "platform": "", "city": "", "date": ""}}
"book ticket for KGF in hyderabad"     -> {"action": "book_movie", "params": {"movie": "KGF", "platform": "", "city": "hyderabad", "date": ""}}
"book movie on bookmyshow"             -> {"action": "book_movie", "params": {"movie": "", "platform": "bookmyshow", "city": "", "date": ""}}
"order pizza for me"                   -> {"action": "order_food", "params": {"item": "pizza", "platform": "", "location": "", "budget": ""}}
"order biryani from swiggy"            -> {"action": "order_food", "params": {"item": "biryani", "platform": "swiggy", "location": "", "budget": ""}}
"play spiderman video"                 -> {"action": "play_media", "params": {"query": "spiderman"}}
"tell me how to make pizza"            -> {"action": "general_chat", "params": {"message": "tell me how to make pizza"}}
"pull gemma3 model"                    -> {"action": "ollama_pull", "params": {"model": "gemma3"}}
"remind me in next 2 minutes to drink water" -> {"action": "schedule_task", "params": {"description": "drink water", "time": "in 2 minutes"}}
"remind me in 5 mins"                  -> {"action": "schedule_task", "params": {"description": "reminder", "time": "in 5 minutes"}}
"turn off wifi"                        -> {"action": "wifi_off", "params": {}}
"turn off" [CONTEXT: bluetooth was turned on] -> {"action": "bluetooth_off", "params": {}}
"is there any videos in my drive"      -> {"action": "find_file", "params": {"query": "videos"}}
"search for python tutorials"          -> {"action": "web_search", "params": {"query": "python tutorials"}}
"yes compose to raju@gmail.com"        -> {"action": "compose_gmail", "params": {"to": "raju@gmail.com", "subject": "", "body": ""}}
"open explorer and search for silica"  -> {"action": "open_explorer_search", "params": {"query": "silica"}}
"play lofi on youtube"                 -> {"action": "search_youtube", "params": {"query": "lofi"}}
"play random video from youtube"       -> {"action": "search_youtube", "params": {"query": "random youtube videos"}}
"stop playing both videos"             -> {"action": "stop_media", "params": {}}
"stop playing"                         -> {"action": "stop_media", "params": {}}
"pause the music"                      -> {"action": "pause_media", "params": {}}
"pause the video"                      -> {"action": "pause_media", "params": {}}
"open swiggy and search for paneer biryani" -> {"action": "open_website", "params": {"site": "swiggy", "query": "paneer biryani"}}
"open swigggy and searchf ro pizza"    -> {"action": "open_website", "params": {"site": "swiggy", "query": "pizza"}}
"search for shoes on amazon"           -> {"action": "open_website", "params": {"site": "amazon", "query": "shoes"}}
"add an item with rating morethan 4 to cart" -> {"action": "general_chat", "params": {"message": "add an item with rating morethan 4 to cart"}}
"click the first search result"        -> {"action": "general_chat", "params": {"message": "click the first search result"}}
"search for strive video in my local pc" -> {"action": "find_file", "params": {"query": "strive"}}
"play strive video from local pc"      -> {"action": "play_media", "params": {"query": "strive"}}
"turn off energy saver mode"             -> {"action": "power_balanced", "params": {}}
"turn on energy saver"                   -> {"action": "power_saver", "params": {}}
"turn on battery saver"                  -> {"action": "power_saver", "params": {}}
"turn off battery saver"                 -> {"action": "power_balanced", "params": {}}
"turn on every saver"                    -> {"action": "power_saver", "params": {}}
"and energy saver"                       -> {"action": "power_saver", "params": {}}
"turn off night light"                   -> {"action": "night_light_off", "params": {}}
"turn on night light mode"               -> {"action": "night_light_on", "params": {}}
"turn on mobile hotspot"                 -> {"action": "hotspot_on", "params": {}}
"disable hotspot"                        -> {"action": "hotspot_off", "params": {}}
"is my hotspot on"                       -> {"action": "hotspot_status", "params": {}}
"make a pdf of my resume"                -> {"action": "convert_to_pdf", "params": {"query": "resume"}}
"convert IKS_Consolidated_Study_Guide.docx to pdf" -> {"action": "convert_to_pdf", "params": {"query": "IKS_Consolidated_Study_Guide.docx"}}
"text file into a pdf fil"               -> {"action": "convert_to_pdf", "params": {"query": "IKS_Consolidated_Study_Guide.docx"}}
"06-10-2026"                             -> {"action": "general_chat", "params": {"message": "06-10-2026"}}
"2026/07/12"                             -> {"action": "general_chat", "params": {"message": "2026/07/12"}}
"15 Jan 2025"                            -> {"action": "general_chat", "params": {"message": "15 Jan 2025"}}
"1234"                                   -> {"action": "general_chat", "params": {"message": "1234"}}
"its wrong"                              -> {"action": "general_chat", "params": {"message": "its wrong"}}
"that's wrong"                           -> {"action": "general_chat", "params": {"message": "that's wrong"}}
"same wrong answers"                     -> {"action": "general_chat", "params": {"message": "same wrong answers"}}
"not right"                              -> {"action": "general_chat", "params": {"message": "not right"}}
"""


import logging

log = logging.getLogger("helios.nl_router")

try:
    from core.routing import RoutingEngine, RoutingContext, RoutingDecision
    _cahra_available = True
except ImportError:
    _cahra_available = False

class NLRouter:
    def __init__(self, llm: HybridLLM):
        self.llm = llm
        if _cahra_available:
            try:
                self.routing_engine = RoutingEngine()
                log.info("CAHRA routing engine loaded into NLRouter successfully.")
            except Exception as e:
                log.error("Failed to load CAHRA routing engine: %s", e)
                self.routing_engine = None
        else:
            self.routing_engine = None
        log.info("NLRouter initialized successfully.")

    def parse(self, user_input: str, context: str = "") -> dict:
        log.info("parse called: user_input='%s'", user_input)

        # ── Fast pre-LLM shortcuts ─────────────────────────────────────────
        # These patterns are unambiguous and must never go to the LLM router.
        _stripped = user_input.strip()

        # Pure date: "06-10-2026", "2026/07/12", "15 Jan 2025", etc.
        _DATE_PATS = [
            re.compile(r'^\d{1,2}[\-/\.]\d{1,2}[\-/\.]\d{2,4}$'),
            re.compile(r'^\d{4}[\-/\.]\d{1,2}[\-/\.]\d{1,2}$'),
            re.compile(r'^\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}$', re.I),
        ]
        if any(p.match(_stripped) for p in _DATE_PATS):
            log.info("parse shortcut: bare date '%s' → general_chat", _stripped)
            return {"action": "general_chat", "params": {"message": _stripped}}

        # Pure number / code (no verb)
        if re.match(r'^[\d\s/\-\.#]+$', _stripped) and len(_stripped) >= 1:
            log.info("parse shortcut: numeric/code input '%s' → general_chat", _stripped)
            return {"action": "general_chat", "params": {"message": _stripped}}

        # Correction phrases → general_chat
        _CORRECTION_PATTERNS = [
            r'\b(its|it\'s|that\'?s|this is|it is)\s+\w*\s*(wrong|incorrect|not right|bad)\b',
            r'\b(its|it\'s|that\'?s|this is|it is)\s+(wrong|incorrect|not right|bad)\b',
            r'\b(wrong|incorrect)\s+(result|answer|response|output|answers)s?\b',
            r'\bsame\s+wrong\b',
            r'^(wrong|incorrect|not right|that\'?s wrong|its wrong|it\'?s wrong)[\s!.]*$',
        ]
        _sl = _stripped.lower()
        # Also catch: short sentence (<=6 words) where 'wrong'/'incorrect' appears
        _sl_words = _sl.split()
        _has_correction_word = any(w in ('wrong', 'incorrect', 'not right') for w in _sl_words)
        if (_has_correction_word and 1 <= len(_sl_words) <= 6
                and not any(w in _sl for w in ('file', 'folder', 'download', 'open', 'play', 'search'))):
            log.info("parse shortcut: correction phrase '%s' → general_chat", _stripped)
            return {"action": "general_chat", "params": {"message": _stripped}}
        if any(re.search(p, _sl) for p in _CORRECTION_PATTERNS):
            log.info("parse shortcut: correction phrase '%s' → general_chat", _stripped)
            return {"action": "general_chat", "params": {"message": _stripped}}

        # Programmatic shortcut for attached files conversion to PDF
        # NOTE: We intentionally do NOT search context for attachment tags.
        # The attachment tag is only injected by the UI into the current message.
        # Searching context caused the shortcut to re-fire on the PREVIOUS session's
        # attachment (e.g. a complaint about images re-triggered a DOCX→PDF conversion).
        attachment_match = re.search(r'\[(DOCX|TXT|DOC|FILE):\s*(.*?)\]', user_input, re.IGNORECASE)

        if attachment_match:
            lower_input = user_input.lower()
            if any(w in lower_input for w in ("convert", "pdf", "make a pdf", "export to pdf", "save as pdf")):
                filename = attachment_match.group(2).strip()
                log.info("Programmatic shortcut match: converting file '%s' to PDF", filename)
                return {"action": "convert_to_pdf", "params": {"query": filename}}
        # ── End fast shortcuts ─────────────────────────────────────────────

        if context:
            prompt = (
                f"Recent conversation (use to resolve follow-ups):\n{context}\n\n"
                f"Route this command: \"{user_input}\""
            )
        else:
            prompt = f'Route this command: "{user_input}"'

        cahra_success = False
        resp = None

        if self.routing_engine:
            try:
                import psutil
                from datetime import datetime
                
                ram_avail = psutil.virtual_memory().available / (1024.0 * 1024.0)
                cpu_p = psutil.cpu_percent()
                active_cloud = self.llm.gemini_model if self.llm.cloud_provider == "gemini" else self.llm.openai_model
                
                now = datetime.now()
                if not hasattr(self, "_last_net_check") or (now - self._last_net_check).total_seconds() > 10:
                    self._cached_internet = self.llm._internet_ok()
                    self._cached_ollama = self.llm._ollama_alive()
                    self._last_net_check = now
                
                routing_context = RoutingContext(
                    prompt=user_input,
                    parsed_intent=None,
                    timestamp=now.isoformat(),
                    internet_available=self._cached_internet,
                    local_model_available=self._cached_ollama,
                    cloud_available=self.llm._has_any_cloud_key(),
                    active_local_model=self.llm.ollama_model,
                    active_cloud_model=active_cloud,
                    operating_system="Windows",
                    cpu_percent=cpu_p,
                    ram_available_mb=ram_avail,
                    gpu_available=False
                )
                
                res = self.routing_engine.route(routing_context)
                best_candidate = res.selected_model
                log.info("CAHRA selected candidate model: '%s' (Decision: %s)", best_candidate, res.decision.value)
                
                orig_mode = self.llm.mode
                orig_model = self.llm.ollama_model
                orig_cloud = self.llm.cloud_provider
                orig_gemini = self.llm.gemini_model
                orig_openai = self.llm.openai_model
                
                try:
                    if res.decision == RoutingDecision.CLOUD:
                        self.llm.mode = "online"
                        if "gemini" in best_candidate:
                            self.llm.cloud_provider = "gemini"
                            self.llm.gemini_model = best_candidate
                        elif "gpt" in best_candidate:
                            self.llm.cloud_provider = "gpt"
                            self.llm.openai_model = best_candidate
                    else:
                        self.llm.mode = "offline"
                        self.llm.ollama_model = best_candidate
                        
                    resp = self.llm.chat(prompt=prompt, system=SYSTEM)
                    cahra_success = True
                    
                    try:
                        from core.routing.routing_diagnostics import RoutingDiagnostics
                        diag = RoutingDiagnostics()
                        if res.decision_snapshot:
                            diag.export_snapshot_json(res.decision_snapshot)
                        diag.export_ranking_json(res.candidate_ranking)
                    except Exception as diag_exc:
                        log.error("Failed to export production CAHRA diagnostics: %s", diag_exc)
                finally:
                    self.llm.mode = orig_mode
                    self.llm.ollama_model = orig_model
                    self.llm.cloud_provider = orig_cloud
                    self.llm.gemini_model = orig_gemini
                    self.llm.openai_model = orig_openai
            except Exception as e:
                log.error("CAHRA routing processing failed. Falling back to legacy: %s", e, exc_info=True)

        if not cahra_success:
            try:
                resp = self.llm.chat(prompt=prompt, system=SYSTEM)
            except Exception as chat_exc:
                log.error("LLM chat request failed inside legacy router fallback: %s", chat_exc, exc_info=True)
                return {"action": "general_chat", "params": {"message": user_input}}

        try:
            text = re.sub(r"```json|```", "", resp.content).strip()
            result = json.loads(text)
            log.info("Successfully routed intent: %s", result)
            return result
        except Exception as exc:
            log.warning("Primary JSON decoding failed for text '%s': %s", text, exc)
            m = re.search(r"\{.*?\}", text, re.DOTALL)
            if m:
                try:
                    result = json.loads(m.group())
                    log.info("Regex extraction successfully routed intent: %s", result)
                    return result
                except Exception as exc2:
                    log.warning("Regex extracted JSON decode failed: %s", exc2)
                    pass
            log.error("Routing failed. Defaulting to general_chat. Raw LLM response: '%s'", resp.content)
        return {"action": "general_chat", "params": {"message": user_input}}
