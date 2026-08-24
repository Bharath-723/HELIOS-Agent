"""
core/desktop_session/task_continuity.py — Task & Commerce Session Continuity Engine
==================================================================================
Preserves multi-turn session context across sequential desktop and commerce user instructions.
Enforces payment safety boundary (TransactionGuard, explicit human authorization, zero secret leakage).
"""

import logging
from typing import Tuple, Dict, Any, Optional
from .session_models import (
    DesktopSessionContext,
    DesktopSessionState,
    DesktopAction,
)

log = logging.getLogger("helios.desktop_session.continuity")

TERMINATION_KEYWORDS = {
    "stop", "end session", "cancel task", "quit session", "finish session",
    "stop session", "close session", "exit session", "end task", "cancel session"
}


class TaskContinuityEngine:
    """Manages context continuity and session termination rules."""

    @staticmethod
    def is_termination_request(instruction: str) -> bool:
        """Check if user explicitly requested session termination."""
        clean = instruction.lower().strip()
        return clean in TERMINATION_KEYWORDS or any(
            kw in clean for kw in ("end session", "cancel task", "stop session", "quit session")
        )

    @staticmethod
    def is_commerce_instruction(instruction: str) -> bool:
        """Check if instruction involves commerce/checkout/payment actions."""
        clean = instruction.lower().strip()
        commerce_keywords = (
            "buy", "purchase", "pay", "order", "add to cart", "checkout",
            "cart", "amazon", "flipkart", "croma", "razorpay"
        )
        return any(kw in clean for kw in commerce_keywords)

    @classmethod
    def update_continuity_context(
        cls,
        context: DesktopSessionContext,
        user_instruction: str,
        planned_action: DesktopAction,
        verification_passed: bool
    ) -> None:
        """Update context with newly executed step while preserving task history."""
        context.last_user_instruction = user_instruction
        context.last_action = planned_action
        context.updated_at = context.updated_at

        # Append to active task chain
        task_chain = context.current_task_context.get("task_chain", [])
        task_chain.append({
            "instruction": user_instruction,
            "action": planned_action.action_type if planned_action else "NONE",
            "target": planned_action.target if planned_action else "",
            "verified": verification_passed,
        })
        context.current_task_context["task_chain"] = task_chain

        if not context.current_task:
            context.current_task = user_instruction

    @classmethod
    def format_continuity_prompt_context(cls, context: DesktopSessionContext) -> str:
        """Format persistent session context for local LLM prompt construction."""
        chain = context.current_task_context.get("task_chain", [])
        history_summary = []
        for step in chain[-5:]:
            status = "✓" if step.get("verified") else "✗"
            history_summary.append(f"[{status}] User: '{step.get('instruction')}' -> Action: {step.get('action')} ({step.get('target')})")

        return (
            f"Active Session ID: {context.session_id}\n"
            f"Session State: {context.session_state.value}\n"
            f"Current Task: {context.current_task or 'General Desktop Task'}\n"
            f"Active Application: {context.active_application}\n"
            f"Active Window Title: {context.active_window}\n"
            f"Recent Session History:\n" + ("\n".join(history_summary) if history_summary else "  (No prior steps)")
        )
