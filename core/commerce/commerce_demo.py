"""
core/commerce/commerce_demo.py — Razorpay Buildathon Demo Engine
=================================================================
Provides deterministic, explainable demonstration scenarios for the Razorpay Buildathon:
1. Full End-to-End Agentic Commerce ("Find wireless keyboard under ₹2000 & buy best one")
2. Direct Payment Flow ("Pay ₹500")
3. Research-Only Intent ("Find useful item under ₹1000 but don't buy anything")
"""

import logging
from typing import Dict, Any
from core.commerce.commerce_models import CommerceContext, CommerceIntentCategory, CommerceState
from core.commerce.commerce_intent import CommerceIntentClassifier
from core.commerce.commerce_researcher import CommerceResearcher
from core.commerce.commerce_comparator import CommerceComparator
from core.commerce.commerce_recommender import CommerceRecommender
from core.commerce.commerce_calculator import CommerceCalculator
from core.commerce.commerce_transaction import CommerceTransactionBridge

log = logging.getLogger("helios.commerce.demo")


class CommerceDemoEngine:
    """Buildathon Demonstration Scenario Runner."""

    @staticmethod
    def run_demo_scenario(prompt: str) -> Dict[str, Any]:
        log.info("CommerceDemoEngine: Running Buildathon Demo for prompt: '%s'", prompt)

        intent = CommerceIntentClassifier.classify(prompt)
        candidates = CommerceResearcher.research(intent)
        comparison = CommerceComparator.compare(intent, candidates)
        recommendation = CommerceRecommender.recommend(intent, comparison)

        res_data = {
            "prompt": prompt,
            "intent": intent.to_dict(),
            "category": intent.category.value,
            "candidates_count": len(candidates),
            "comparison": comparison.to_dict(),
            "recommendation": recommendation.to_dict() if recommendation else None,
            "stop_before_transaction": intent.category == CommerceIntentCategory.INFORMATION_ONLY or intent.explicit_no_buy
        }

        if recommendation and not res_data["stop_before_transaction"]:
            cost = CommerceCalculator.calculate(recommendation.selected_candidate)
            bridge = CommerceTransactionBridge()
            prep_res = bridge.prepare_transaction(intent, recommendation, cost)

            res_data["cost"] = cost.to_dict()
            res_data["transaction_prepared"] = True
            res_data["prepared_payload"] = prep_res

        return res_data
