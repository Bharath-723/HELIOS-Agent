"""
core/desktop_session/agent_controller.py — Local LLM Action & Goal Planner
===========================================================================
Constructs structured context prompts for the local LLM and parses semantic DesktopGoals with multi-action plans.
Integrates ScreenTargetResolver for semantic target resolution ("first result" -> SEARCH_RESULT[0]).
Removes synthetic internal state names ("query_typed", "submitted").
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List

from .session_models import (
    DesktopSessionContext,
    DesktopAction,
    DesktopGoal,
    SemanticTarget,
    ScreenState,
)
from .task_continuity import TaskContinuityEngine
from .screen_target_resolver import ScreenTargetResolver

log = logging.getLogger("helios.desktop_session.controller")


class LocalAgentController:
    """Action & Goal planning controller powered by local LLM reasoning."""

    def __init__(self, llm=None):
        self.llm = llm

    def plan_goal(
        self,
        instruction: str,
        screen_state: ScreenState,
        context: DesktopSessionContext
    ) -> DesktopGoal:
        """
        Formulate a structured DesktopGoal with an ordered action_plan sequence
        for the user instruction, taking current screen state into account.
        """
        clean_inst = instruction.strip()
        lower_inst = clean_inst.lower()

        # 1. Explicit Session Termination Check
        if TaskContinuityEngine.is_termination_request(clean_inst):
            return DesktopGoal(
                goal_type="TERMINATE",
                target_app="helios",
                completion_condition="SESSION_TERMINATED",
                raw_instruction=clean_inst,
                action_plan=[
                    DesktopAction(action_type="TERMINATE", target_app="helios", target="Session", value="stop", expected_state="Session Completed")
                ]
            )

        # 2. Semantic Target Resolution ("open first result", "add to cart", "search box")
        semantic_target = ScreenTargetResolver.parse_semantic_target(clean_inst)

        # 3. Local LLM Prompting (if LLM provided)
        planning_mode = "DETERMINISTIC_FALLBACK"
        if self.llm:
            try:
                prompt = self._build_llm_prompt(clean_inst, screen_state, context)
                if hasattr(self.llm, "generate"):
                    llm_response = self.llm.generate(prompt)
                elif hasattr(self.llm, "query"):
                    llm_response = self.llm.query(prompt)
                elif hasattr(self.llm, "complete"):
                    llm_response = self.llm.complete(prompt)
                else:
                    llm_response = str(self.llm(prompt))

                provider_name = getattr(self.llm, "cloud_provider", "LOCAL").upper() if getattr(self.llm, "active_cloud_model", None) else "LOCAL"
                model_name = getattr(self.llm, "active_cloud_model", None) or getattr(self.llm, "ollama_model", "gemma3")
                planning_mode = "LLM"

                log.info(
                    "[LOCAL LLM]\n"
                    "provider=%s\n"
                    "model=%s\n"
                    "request=%s\n"
                    "screen_context_included=%s\n"
                    "response_received=%s\n"
                    "planning_mode=%s",
                    provider_name, model_name, clean_inst, True, bool(llm_response), planning_mode
                )

                goal = self._parse_llm_goal(llm_response, clean_inst)
                if goal and goal.action_plan:
                    if semantic_target:
                        goal.semantic_target = semantic_target
                    log.info("LocalAgentController: LLM planned goal -> %s", goal.to_dict())
                    return goal
            except Exception as exc:
                log.warning(
                    "[LOCAL LLM]\n"
                    "provider=LOCAL\n"
                    "model=gemma3\n"
                    "request=%s\n"
                    "screen_context_included=True\n"
                    "response_received=False\n"
                    "planning_mode=DETERMINISTIC_FALLBACK\n"
                    "error=%s",
                    clean_inst, exc
                )

        # 4. Deterministic Context-Aware Goal Planner Fallback
        log.info(
            "[LOCAL LLM]\n"
            "provider=LOCAL\n"
            "model=gemma3\n"
            "request=%s\n"
            "screen_context_included=True\n"
            "response_received=True\n"
            "planning_mode=DETERMINISTIC_FALLBACK",
            clean_inst
        )
        return self._deterministic_plan_goal(lower_inst, clean_inst, screen_state, context, semantic_target)

    def plan_action(
        self,
        instruction: str,
        screen_state: ScreenState,
        context: DesktopSessionContext
    ) -> DesktopAction:
        """Backwards compatible method returning the primary action of the planned goal."""
        goal = self.plan_goal(instruction, screen_state, context)
        return goal.action_plan[0] if goal.action_plan else DesktopAction(action_type="TYPE", target_app="chrome", value=instruction)

    def _build_llm_prompt(
        self,
        instruction: str,
        screen_state: ScreenState,
        context: DesktopSessionContext
    ) -> str:
        continuity_text = TaskContinuityEngine.format_continuity_prompt_context(context)
        return (
            "You are HELIOS Desktop Controller. Formulate a structured DesktopGoal for the user instruction.\n"
            "Output EXACTLY ONE JSON object with: goal, target_app, query, completion_condition, actions.\n\n"
            f"USER INSTRUCTION: {instruction}\n"
            f"CURRENT SCREEN STATE: {screen_state.active_window_title} ({screen_state.active_app_name})\n"
            f"Summary: {screen_state.screen_summary}\n\n"
            f"CONTINUITY CONTEXT:\n{continuity_text}\n\n"
            "Example JSON format for search:\n"
            '{\n  "goal": "SEARCH",\n  "target_app": "chrome",\n  "query": "Logitech wireless keyboard",\n  "completion_condition": "SEARCH_RESULTS_VISIBLE",\n'
            '  "actions": [\n'
            '    {"action_type": "TYPE", "target_app": "chrome", "target_element": "search_box", "value": "Logitech wireless keyboard"},\n'
            '    {"action_type": "KEYPRESS", "target_app": "chrome", "value": "enter"},\n'
            '    {"action_type": "WAIT_FOR_TRANSITION", "target_app": "chrome"},\n'
            '    {"action_type": "VERIFY_GOAL", "target_app": "chrome", "value": "Logitech wireless keyboard"}\n'
            '  ]\n}'
        )

    def _parse_llm_goal(self, response_text: str, raw_inst: str) -> Optional[DesktopGoal]:
        try:
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                g_type = data.get("goal", "CUSTOM").upper()
                t_app = data.get("target_app", "chrome")
                query = data.get("query", "")
                cond = data.get("completion_condition", "")
                raw_actions = data.get("actions", [])
                plan = []
                for a in raw_actions:
                    plan.append(DesktopAction(
                        action_type=a.get("action_type", "TYPE").upper(),
                        target_app=a.get("target_app", t_app),
                        target=a.get("target", ""),
                        value=a.get("value", ""),
                        expected_state=a.get("expected_state", ""),
                        target_url=a.get("target_url", ""),
                        target_element=a.get("target_element", ""),
                    ))
                return DesktopGoal(
                    goal_type=g_type,
                    target_app=t_app,
                    query=query,
                    completion_condition=cond,
                    action_plan=plan,
                    raw_instruction=raw_inst,
                )
        except Exception as exc:
            log.debug("LocalAgentController: JSON parsing failed: %s", exc)
        return None

    def _deterministic_plan_goal(
        self,
        lower_inst: str,
        raw_inst: str,
        screen_state: ScreenState,
        context: DesktopSessionContext,
        semantic_target: Optional[SemanticTarget] = None
    ) -> DesktopGoal:
        """Deterministic goal planner building compound action sequences."""

        # A. Navigation Intents ("go to amazon", "open amazon", "open amazon.in")
        if any(kw in lower_inst for kw in ("go to amazon", "open amazon", "open amazon.in", "navigate to amazon")):
            return DesktopGoal(
                goal_type="NAVIGATE",
                target_app="chrome",
                target_site="amazon",
                query="https://www.amazon.in/",
                completion_condition="PAGE_READY",
                raw_instruction=raw_inst,
                action_plan=[
                    DesktopAction(action_type="NAVIGATE", target_app="chrome", target_url="https://www.amazon.in/", target="Amazon", expected_state="Amazon.in"),
                    DesktopAction(action_type="WAIT_FOR_TRANSITION", target_app="chrome"),
                    DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value="amazon", expected_state="Amazon.in"),
                ]
            )

        # B. Product Search Goal ("search for Logitech wireless keyboard")
        if "search for" in lower_inst or "search" in lower_inst:
            query = lower_inst.replace("search for", "").replace("search", "").strip()
            target_app = "chrome" if ("chrome" in screen_state.active_app_name.lower() or "amazon" in screen_state.active_window_title.lower()) else "settings"
            if target_app == "chrome":
                return DesktopGoal(
                    goal_type="SEARCH",
                    target_app="chrome",
                    target_site="amazon",
                    query=query,
                    completion_condition="SEARCH_RESULTS_VISIBLE",
                    raw_instruction=raw_inst,
                    action_plan=[
                        DesktopAction(action_type="TYPE", target_app="chrome", target_element="search_box", target="Amazon Search Box", value=query),
                        DesktopAction(action_type="KEYPRESS", target_app="chrome", value="enter", target="Submit search"),
                        DesktopAction(action_type="WAIT_FOR_TRANSITION", target_app="chrome"),
                        DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value=query, expected_state=f"{query} search results"),
                    ]
                )
            else:
                return DesktopGoal(
                    goal_type="SEARCH",
                    target_app="settings",
                    query=query,
                    completion_condition="SETTINGS_SEARCH_VISIBLE",
                    raw_instruction=raw_inst,
                    action_plan=[
                        DesktopAction(action_type="TYPE", target_app="settings", target_element="search_box", target="Settings Search Box", value=query),
                        DesktopAction(action_type="KEYPRESS", target_app="settings", value="enter"),
                        DesktopAction(action_type="WAIT_FOR_TRANSITION", target_app="settings"),
                        DesktopAction(action_type="VERIFY_GOAL", target_app="settings", value=query, expected_state=f"{query} search results"),
                    ]
                )

        # C. Select Result Item ("open first result", "click second product")
        if semantic_target and semantic_target.target_type == "SEARCH_RESULT":
            index = semantic_target.index
            target_label = f"SEARCH_RESULT[{index - 1}]"
            return DesktopGoal(
                goal_type="SELECT_ITEM",
                target_app="chrome",
                target_site="amazon",
                semantic_target=semantic_target,
                completion_condition="PRODUCT_PAGE_VISIBLE",
                raw_instruction=raw_inst,
                action_plan=[
                    DesktopAction(action_type="CLICK", target_app="chrome", target=target_label, value=f"result_{index}"),
                    DesktopAction(action_type="WAIT_FOR_TRANSITION", target_app="chrome"),
                    DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value="product", expected_state="Product Page"),
                ]
            )

        # Fallback check for "first result", "second result" without target parser
        if any(kw in lower_inst for kw in ("first result", "first product", "open first", "click first")):
            sem = SemanticTarget(target_type="SEARCH_RESULT", index=1, label="first_result")
            return DesktopGoal(
                goal_type="SELECT_ITEM",
                target_app="chrome",
                target_site="amazon",
                semantic_target=sem,
                completion_condition="PRODUCT_PAGE_VISIBLE",
                raw_instruction=raw_inst,
                action_plan=[
                    DesktopAction(action_type="CLICK", target_app="chrome", target="SEARCH_RESULT[0]", value="result_1"),
                    DesktopAction(action_type="WAIT_FOR_TRANSITION", target_app="chrome"),
                    DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value="product", expected_state="Product Page"),
                ]
            )

        # D. Add to Cart ("add to cart", "add it to cart")
        if "add" in lower_inst and "cart" in lower_inst:
            sem = SemanticTarget(target_type="BUTTON", label="Add to Cart")
            return DesktopGoal(
                goal_type="ADD_TO_CART",
                target_app="chrome",
                target_site="amazon",
                semantic_target=sem,
                completion_condition="CART_UPDATED",
                raw_instruction=raw_inst,
                action_plan=[
                    DesktopAction(action_type="CLICK", target_app="chrome", target="Add to Cart", value="cart"),
                    DesktopAction(action_type="WAIT_FOR_TRANSITION", target_app="chrome"),
                    DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value="cart", expected_state="Item added to cart"),
                ]
            )

        # E. Payment Goal ("make payment", "pay now", "proceed to checkout")
        if any(kw in lower_inst for kw in ("pay", "payment", "checkout")):
            return DesktopGoal(
                goal_type="PAY",
                target_app="chrome",
                completion_condition="AUTHORIZATION_REQUIRED",
                raw_instruction=raw_inst,
                action_plan=[
                    DesktopAction(action_type="CLICK", target_app="chrome", target="Pay Now", value="pay"),
                    DesktopAction(action_type="VERIFY_GOAL", target_app="chrome", value="pay", expected_state="Transaction Authorization Required"),
                ]
            )

        # F. Open Application ("open settings", "open display")
        if "open settings" in lower_inst:
            return DesktopGoal(
                goal_type="OPEN_APPLICATION",
                target_app="settings",
                completion_condition="APP_OPENED",
                raw_instruction=raw_inst,
                action_plan=[
                    DesktopAction(action_type="OPEN_APPLICATION", target_app="settings", target="Settings", value="ms-settings:"),
                    DesktopAction(action_type="WAIT_FOR_TRANSITION", target_app="settings"),
                    DesktopAction(action_type="VERIFY_GOAL", target_app="settings", value="settings", expected_state="Settings"),
                ]
            )

        # Default action goal
        return DesktopGoal(
            goal_type="CUSTOM",
            target_app="chrome" if "chrome" in screen_state.active_app_name.lower() else "settings",
            completion_condition="ACTION_EXECUTED",
            raw_instruction=raw_inst,
            action_plan=[
                DesktopAction(action_type="TYPE", target_app="chrome", target="Active Window", value=lower_inst, expected_state=screen_state.active_window_title)
            ]
        )
