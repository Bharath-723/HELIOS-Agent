"""
core/context_resolver.py — HELIOS Structured Context Engine
============================================================
Maintains conversation state, active entities, previous actions,
and resolves ambiguous contextual references (pronouns, references)
without hardcoding single-purpose rules or bypassing CAHRA/NLRouter.
"""

import re
import logging
from typing import Dict, Any, Optional, List

log = logging.getLogger("helios.context_resolver")

PRONOUN_PATS = [
    re.compile(r'\b(it|this|that|them|there|the file|the app|the document|the previous one|the first result)\b', re.I),
    re.compile(r'^\s*(now\s+)?(turn\s+off\s+it|turn\s+it\s+off|close\s+it|open\s+it|delete\s+it|rename\s+it|run\s+it)\s*$', re.I)
]

class ContextState:
    """Structured context container representing current session state."""
    def __init__(self):
        self.previous_user_request: str = ""
        self.previous_helios_response: str = ""
        self.active_intent: str = ""
        self.previous_action: str = ""
        self.active_entity: str = ""
        self.active_application: str = ""
        self.last_referenced_file: str = ""
        self.last_search_query: str = ""

    def update_from_turn(self, user_msg: str, helios_msg: str, action: str = "", params: dict = None) -> None:
        if params is None:
            params = {}
        self.previous_user_request = user_msg
        self.previous_helios_response = helios_msg
        if action:
            self.previous_action = action
            self.active_intent = action

        # Entity extraction from action & params
        lower_u = user_msg.lower()
        lower_h = helios_msg.lower()

        if "bluetooth" in lower_u or "bluetooth" in lower_h:
            self.active_entity = "bluetooth"
        elif "wifi" in lower_u or "wifi" in lower_h:
            self.active_entity = "wifi"
        elif "night light" in lower_u or "night light" in lower_h:
            self.active_entity = "night light"
        elif "hotspot" in lower_u or "hotspot" in lower_h:
            self.active_entity = "hotspot"
        elif "chrome" in lower_u or "chrome" in lower_h:
            self.active_entity = "chrome"
            self.active_application = "chrome"
        elif "settings" in lower_u or "settings" in lower_h:
            self.active_entity = "settings"
            self.active_application = "settings"
        elif params.get("app"):
            self.active_entity = params["app"]
            self.active_application = params["app"]
        elif params.get("name"):
            self.active_entity = params["name"]
            self.last_referenced_file = params["name"]
        elif params.get("filename"):
            self.active_entity = params["filename"]
            self.last_referenced_file = params["filename"]
        elif params.get("query"):
            self.last_search_query = params["query"]


class ContextResolver:
    """Confidence-aware context resolution engine."""

    def __init__(self):
        self.state = ContextState()

    def update(self, user_msg: str, helios_msg: str, action: str = "", params: dict = None) -> None:
        """Update context state after each turn."""
        self.state.update_from_turn(user_msg, helios_msg, action, params)
        log.info("Context updated: active_entity='%s', previous_action='%s'",
                 self.state.active_entity, self.state.previous_action)

    def is_context_dependent(self, prompt: str) -> bool:
        """Returns True if prompt contains pronouns or short context reference phrases."""
        p_lower = prompt.strip().lower()
        if any(pat.search(p_lower) for pat in PRONOUN_PATS):
            return True
        short_cmds = {"turn off", "turn on", "close it", "open it", "stop it", "run it", "now turn off", "now turn on"}
        if p_lower in short_cmds:
            return True
        return False

    def build_enriched_context(self, prompt: str, history_messages: List[Dict[str, str]]) -> str:
        """
        Builds structured context string for NLRouter & CAHRA.
        Includes active entity, previous action, and recent conversation turns.
        """
        lines = []
        if self.state.active_entity:
            lines.append(f"[Active Entity: {self.state.active_entity}]")
        if self.state.previous_action:
            lines.append(f"[Previous Action: {self.state.previous_action}]")
        if self.state.last_referenced_file:
            lines.append(f"[Last Referenced File: {self.state.last_referenced_file}]")
        if self.state.active_application:
            lines.append(f"[Active Application: {self.state.active_application}]")

        recent = history_messages[-6:]
        for m in recent:
            role_label = "User" if m.get("role") == "user" else "HELIOS"
            content = m.get("content", "")[:300]
            lines.append(f"{role_label}: {content}")

        return "\n".join(lines)
