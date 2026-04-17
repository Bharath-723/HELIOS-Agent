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

════════════════════════════════════════════════
ACTIONS:
════════════════════════════════════════════════

play_media: {"query": "name"}
open_app: {"app": "app name"}
open_explorer_search: {"query": "name"}
open_website: {"site": "name"}
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
brightness_set: {"level": 70}
brightness_up: {"amount": 10}
brightness_down: {"amount": 10}
volume_up: {"steps": 5}
volume_down: {"steps": 5}
mute: {}
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
open_settings: {"page": "wifi|bluetooth|display|sound|battery|updates|airplane"}
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
"""


class NLRouter:
    def __init__(self, llm: HybridLLM):
        self.llm = llm

    def parse(self, user_input: str, context: str = "") -> dict:
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
