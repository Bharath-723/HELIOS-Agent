"""
core/commerce/commerce_intent.py — Commercial Intent Classifier
================================================================
Classifies user commercial requests into Information-Only, Purchase Preparation,
Purchase Request, or Payment-Only with budget and constraint extraction.
"""

import re
import logging
from typing import Optional, Dict, Any, List
from core.commerce.commerce_models import CommerceIntent, CommerceIntentCategory

log = logging.getLogger("helios.commerce.intent")


class CommerceIntentClassifier:
    """Classifies commercial intent from natural language prompts."""

    @staticmethod
    def classify(prompt: str) -> CommerceIntent:
        raw = prompt.strip()
        lower = raw.lower()

        # Check for explicit "don't buy" / "do not purchase" / informational constraints
        explicit_no_buy = any(kw in lower for kw in (
            "don't buy", "dont buy", "do not buy", "don't purchase", "dont purchase",
            "do not purchase", "just research", "only research", "recommendation only",
            "just show me", "don't pay yet", "just prepare"
        ))

        # Check for payment-only requests (e.g., "pay ₹500")
        is_payment_only = any(re.search(r'\b' + re.escape(v) + r'\b', lower) for v in (
            "pay", "make payment", "send money"
        )) and not any(kw in lower for kw in ("keyboard", "gift", "product", "item", "find", "search", "compare", "recommend"))

        if is_payment_only and not explicit_no_buy and ("₹" in raw or "rs" in lower or "inr" in lower or re.search(r'\d+', lower)):
            amount = CommerceIntentClassifier._extract_budget(raw)
            return CommerceIntent(
                raw_prompt=raw,
                category=CommerceIntentCategory.PAYMENT_ONLY,
                target_item="Direct Payment",
                budget_limit_inr=amount,
                explicit_purchase_requested=True
            )

        # Check for explicit purchase verbs ("buy", "purchase", "checkout", "order")
        has_purchase_verb = any(re.search(r'\b' + re.escape(v) + r'\b', lower) for v in (
            "buy", "purchase", "checkout", "order", "get me", "buy it"
        ))

        # Check for informational questions ("what is", "compare these", "find me", "show me", "how much")
        is_question = lower.startswith(("what", "how", "which", "where", "can you show", "compare")) or "what is the best" in lower

        # Extract budget constraint (e.g. under ₹2000, for ₹500, under 1000)
        budget = CommerceIntentClassifier._extract_budget(raw)

        # Extract target item description
        target_item = CommerceIntentClassifier._extract_target_item(raw)

        # Determine Category
        if explicit_no_buy or (is_question and not has_purchase_verb and "prepare" not in lower):
            category = CommerceIntentCategory.INFORMATION_ONLY
        elif "prepare" in lower and not any(re.search(r'\b' + re.escape(v) + r'\b', lower) for v in ("buy it", "buy the best", "checkout")):
            category = CommerceIntentCategory.PURCHASE_PREPARATION
        elif has_purchase_verb and not explicit_no_buy:
            category = CommerceIntentCategory.PURCHASE_REQUEST
        else:
            category = CommerceIntentCategory.INFORMATION_ONLY

        constraints = CommerceIntentClassifier._extract_constraints(raw, budget)

        return CommerceIntent(
            raw_prompt=raw,
            category=category,
            target_item=target_item,
            budget_limit_inr=budget,
            explicit_purchase_requested=(category == CommerceIntentCategory.PURCHASE_REQUEST),
            explicit_no_buy=explicit_no_buy,
            extracted_constraints=constraints
        )

    @staticmethod
    def _extract_budget(text: str) -> Optional[float]:
        # Match patterns like: under ₹2000, under 2,000, for ₹500, max ₹1000, budget ₹1500
        m = re.search(r'(?:under|below|for|within|max|budget(?: of)?|less than)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', text, re.IGNORECASE)
        if m:
            val_str = m.group(1).replace(',', '')
            try:
                val = float(val_str)
                if val > 0:
                    return val
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_target_item(text: str) -> str:
        # Strip common action verbs & budget phrases to get item title
        clean = re.sub(r'\b(find|search|compare|recommend|buy|purchase|pay|for|me|a|the|best|good|useful|item|product|under|below|within|rs\.?|inr|₹|\d+)\b', '', text, flags=re.IGNORECASE)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean if clean else "Requested Item"

    @staticmethod
    def _extract_constraints(text: str, budget: Optional[float]) -> List[str]:
        constraints = []
        if budget:
            constraints.append(f"Price ≤ ₹{budget:,.2f}")
        lower = text.lower()
        if "wireless" in lower:
            constraints.append("Connectivity: Wireless")
        if "mechanical" in lower:
            constraints.append("Type: Mechanical")
        if "rgb" in lower:
            constraints.append("Lighting: RGB")
        if "rechargeable" in lower:
            constraints.append("Power: Rechargeable")
        return constraints
