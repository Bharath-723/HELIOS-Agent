"""
core/commerce/commerce_memory.py — Commerce Memory Integration
================================================================
Records verified purchases in HELIOS L3/L4 Knowledge & Memory system.
Strictly excludes secrets, private keys, API keys, or raw signatures.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from core.commerce.commerce_models import CommerceContext

log = logging.getLogger("helios.commerce.memory")


class CommerceMemoryRecorder:
    """Stores verified commercial transactions into persistent memory."""

    @staticmethod
    def record_transaction(context: CommerceContext) -> Dict[str, Any]:
        if not context.recommendation or not context.cost:
            return {"success": False, "message": "Incomplete context"}

        item_name = context.recommendation.selected_candidate.name
        merchant = context.recommendation.selected_candidate.merchant
        amount_inr = context.cost.total_inr
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        memory_summary = f"User purchased {item_name} from {merchant} for ₹{amount_inr:,.2f} via Razorpay on {timestamp}."

        log.info("CommerceMemoryRecorder: Recording memory entry: '%s'", memory_summary)

        # Attempt recording into HELIOS knowledge layer if available
        try:
            from core.knowledge.knowledge_engine import KnowledgeEngine
            ke = KnowledgeEngine()
            ke.add_memory_entry(
                layer="L3_PERSISTENT",
                content=memory_summary,
                tags=["commerce", "purchase", "razorpay", merchant.lower()]
            )
        except Exception as exc:
            log.warning("CommerceMemoryRecorder: Optional KnowledgeEngine integration note: %s", exc)

        return {
            "success": True,
            "memory_summary": memory_summary,
            "timestamp": timestamp
        }
