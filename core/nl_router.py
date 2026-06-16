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

════════════════════════════════════════════════
ACTIONS:
════════════════════════════════════════════════

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
"""


class NLRouter:
    def __init__(self, llm: HybridLLM):
        self.llm = llm

    def parse(self, user_input: str, context: str = "") -> dict:
        # Programmatic shortcut for attached files conversion to PDF
        attachment_match = re.search(r'\[(DOCX|TXT|DOC|FILE):\s*(.*?)\]', user_input, re.IGNORECASE)
        if not attachment_match and context:
            attachment_match = re.search(r'\[(DOCX|TXT|DOC|FILE):\s*(.*?)\]', context, re.IGNORECASE)
            
        if attachment_match:
            lower_input = user_input.lower()
            if any(w in lower_input for w in ("convert", "pdf", "make a pdf", "export to pdf", "save as pdf")):
                filename = attachment_match.group(2).strip()
                return {"action": "convert_to_pdf", "params": {"query": filename}}

        if context:
            prompt = (
                f"Recent conversation (use to resolve follow-ups):\n{context}\n\n"
                f"Route this command: \"{user_input}\""
            )
        else:
            prompt = f'Route this command: "{user_input}"'

        resp = self.llm.chat(prompt=prompt, system=SYSTEM)
        text = re.sub(r"```json|```", "", resp.content).strip()
        try:
            return json.loads(text)
        except Exception:
            m = re.search(r"\{.*?\}", text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except Exception:
                    pass
        return {"action": "general_chat", "params": {"message": user_input}}
