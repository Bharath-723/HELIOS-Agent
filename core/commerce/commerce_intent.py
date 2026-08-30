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
        quantity = CommerceIntentClassifier._extract_quantity(raw)
        target_item = CommerceIntentClassifier._extract_target_item(raw)
        requested_model = CommerceIntentClassifier._extract_requested_model(raw)

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
        if requested_model:
            constraints.append(f"Model: {requested_model.upper()}")

        return CommerceIntent(
            raw_prompt=raw,
            category=category,
            target_item=target_item,
            budget_limit_inr=budget,
            quantity=quantity,
            requested_model=requested_model,
            explicit_purchase_requested=(category == CommerceIntentCategory.PURCHASE_REQUEST),
            explicit_no_buy=explicit_no_buy,
            extracted_constraints=constraints
        )

    @staticmethod
    def _extract_requested_model(text: str) -> Optional[str]:
        # Match explicit model tokens e.g. K120, K380, M221, Key2, PS-301, C300, etc.
        models = re.findall(r'\b(k120|k380|m221|key2|deuce|konnect c|[a-z]\d{2,4}|\d{3,4}[a-z]?)\b', text.lower())
        if models:
            # Avoid matching plain numbers like 499 or 100
            for m in models:
                if not m.isdigit():
                    return m
        return None

    @staticmethod
    def _extract_budget(text: str) -> Optional[float]:
        # Match ONLY explicit price patterns (currency symbol OR explicit budget/price keyword)
        # e.g., ₹499, Rs. 500, INR 1200, under 2000, for ₹499, priced at 500
        pats = [
            r'(?:₹|rs\.?|inr)\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)',
            r'\b(?:under|below|within|max|budget(?: of)?|less than|around|priced at)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)\b',
            r'\b(?:for|at)\s+(?:₹|rs\.?|inr)\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)\b'
        ]
        for pat in pats:
            m = re.search(pat, text, re.IGNORECASE)
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
    def _extract_quantity(text: str) -> int:
        # Match patterns like: 2 units, 3 pieces, purchase 2, buy 4
        m_qty = re.search(r'\b(?:buy|purchase|order|get)\s+(\d{1,3})\b(?!\s*(?:rs|inr|rupees|rupee|\$))', text, re.IGNORECASE)
        if m_qty:
            try:
                q = int(m_qty.group(1))
                if 1 <= q <= 1000:
                    return q
            except ValueError:
                pass
        m_units = re.search(r'\b(\d{1,3})\s*(?:units?|pcs?|pieces?|pack|packs?)\b', text, re.IGNORECASE)
        if m_units:
            try:
                q = int(m_units.group(1))
                if 1 <= q <= 1000:
                    return q
            except ValueError:
                pass
        return 1

    @staticmethod
    def _extract_target_item(text: str) -> str:
        # Strip budget phrases first (e.g. for ₹499, under 2000, for 500, max 1000)
        clean = re.sub(r'\b(?:under|below|within|max|budget(?: of)?|less than|priced at|for|at)\s*(?:₹|rs\.?|inr)?\s*\d+(?:,\d{3})*(?:\.\d{1,2})?\b', '', text, flags=re.IGNORECASE)
        clean = re.sub(r'(?:₹|rs\.?|inr)\s*\d+(?:,\d{3})*(?:\.\d{1,2})?', '', clean, flags=re.IGNORECASE)
        # Strip action verbs and generic keywords, preserving model names/numbers
        clean = re.sub(r'\b(find|search|compare|recommend|buy|purchase|pay|checkout|order|prepare|the|payment|me|a|the|best|good|useful|item|product|units?|of|at|listed|price)\b', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+', ' ', clean).strip(' .,!?:;')
        return clean if len(clean) >= 2 else "Requested Item"

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
