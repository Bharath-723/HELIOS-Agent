"""
HELIOS v2 - Intent Understanding Engine
Extracts goals, categories, and resource requirements from prompt text.
"""
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.reasoning.reasoning_models import TaskIntent, TaskCategory

log = logging.getLogger("helios.reasoning.intent")

class IntentUnderstandingEngine:
    def __init__(self, rules_path: Optional[str] = None):
        if rules_path is None:
            rules_path = str(Path(__file__).parent / "planning_rules.json")
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            log.error("Failed to load planning rules: %s", exc)
            return {}

    def parse(self, prompt: str) -> TaskIntent:
        prompt_lower = prompt.lower().strip()
        log.info("Analyzing user intent for prompt='%s'", prompt)

        # 1. Goal Extraction (Rule-based heuristics)
        primary_goal = prompt
        secondary_goal = None
        
        # Split multi-step workflows like "search X and save to Y"
        conjunctions = [" and then ", " and save it to ", " and summarize ", " then ", " and add it to "]
        for conj in conjunctions:
            if conj in prompt_lower:
                idx = prompt_lower.find(conj)
                part1 = prompt[:idx].strip()
                part2 = prompt[idx + len(conj):].strip()
                primary_goal = part1
                secondary_goal = part2
                break

        # 2. Category Classification
        assigned_category = TaskCategory.CHAT
        max_score = 0
        categories_config = self.rules.get("categories", {})
        
        matched_categories = []
        for cat_name, config in categories_config.items():
            keywords = config.get("keywords", [])
            score = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', prompt_lower))
            if score > 0:
                matched_categories.append((cat_name, score))
                if score > max_score:
                    max_score = score
                    assigned_category = TaskCategory(cat_name)

        # Handle mixed workloads (multiple distinct category matches)
        if len(matched_categories) > 1 and max_score > 0:
            assigned_category = TaskCategory.MIXED

        # 3. Privacy & Internet Requirements
        intent_rules = self.rules.get("intent_rules", {})
        freshness_indicators = intent_rules.get("freshness_indicators", [])
        privacy_indicators = intent_rules.get("privacy_indicators", [])

        requires_internet = any(re.search(r'\b' + re.escape(fi) + r'\b', prompt_lower) for fi in freshness_indicators)
        # Check if the matched category configuration requires internet
        if assigned_category != TaskCategory.MIXED and assigned_category != TaskCategory.CHAT:
            cat_config = categories_config.get(assigned_category.value, {})
            if cat_config.get("internet_requirement", False):
                requires_internet = True
        
        # Override internet if prompt explicitly contains web indicators
        if any(kw in prompt_lower for kw in ["google", "youtube", "online", "search the web", "url"]):
            requires_internet = True

        contains_sensitive = any(re.search(r'\b' + re.escape(pi) + r'\b', prompt_lower) for pi in privacy_indicators)
        privacy_req = "low"
        if contains_sensitive:
            privacy_req = "high"
        elif assigned_category in (TaskCategory.FILE, TaskCategory.NOTES) or any(c in ["file", "notes"] for c, _ in matched_categories):
            privacy_req = "medium"

        # 4. Tool requirements
        required_tools = []
        if assigned_category == TaskCategory.MIXED:
            for cat_name, _ in matched_categories:
                tool = categories_config.get(cat_name, {}).get("default_tool")
                if tool:
                    required_tools.append(tool)
        else:
            tool = categories_config.get(assigned_category.value, {}).get("default_tool")
            if tool:
                required_tools.append(tool)

        # 5. Output structure expectation
        if any(w in prompt_lower for w in ["note", "file", "document", "docx", "pdf"]):
            expected_output = "structured_file"
        elif any(w in prompt_lower for w in ["schedule", "remind", "timer"]):
            expected_output = "scheduler_confirmation"
        elif any(w in prompt_lower for w in ["search", "find", "google"]):
            expected_output = "search_results_summary"
        else:
            expected_output = "text_response"

        # 6. Complexity Heuristics
        base_complexity = 0.2
        if assigned_category == TaskCategory.MIXED:
            base_complexity = 0.7
        elif secondary_goal:
            base_complexity = 0.5
        elif any(w in prompt_lower for w in ["complex", "analyze", "explain", "code", "summarize"]):
            base_complexity = 0.6
        else:
            base_complexity = categories_config.get(assigned_category.value, {}).get("complexity", 0.3)

        # 7. Urgency Level
        urgency = "low"
        if any(w in prompt_lower for w in ["urgent", "immediately", "quick", "fast", "now"]):
            urgency = "high"

        return TaskIntent(
            primary_goal=primary_goal,
            secondary_goal=secondary_goal,
            category=assigned_category,
            privacy_requirement=privacy_req,
            requires_internet=requires_internet,
            requires_tools=required_tools,
            expected_output=expected_output,
            complexity_score=base_complexity,
            urgency_level=urgency
        )
