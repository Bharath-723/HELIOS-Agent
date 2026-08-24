"""
core/commerce/commerce_orchestrator.py — Agentic Commerce Orchestrator
========================================================================
Central orchestrator driving the 16-state commercial transaction lifecycle:
DISCOVERING -> UNDERSTANDING -> RESEARCHING -> COMPARING -> RECOMMENDING ->
CALCULATING -> TRANSACTION_PREPARED -> REQUIRES_AUTHORIZATION -> AUTHORIZED ->
CHECKOUT_OPEN -> PAYMENT_PROCESSING -> VERIFYING -> VERIFIED -> MEMORY_UPDATED -> COMPLETED.
"""

import uuid
import logging
from typing import Dict, Any, Optional
from core.commerce.commerce_models import (
    CommerceContext, CommerceState, CommerceIntentCategory
)
from core.commerce.commerce_intent import CommerceIntentClassifier
from core.commerce.commerce_researcher import CommerceResearcher
from core.commerce.commerce_comparator import CommerceComparator
from core.commerce.commerce_recommender import CommerceRecommender
from core.commerce.commerce_calculator import CommerceCalculator
from core.commerce.commerce_transaction import CommerceTransactionBridge
from core.commerce.commerce_authorization import CommerceAuthorizationGuard
from core.commerce.commerce_verifier import CommerceVerifier
from core.commerce.commerce_memory import CommerceMemoryRecorder
from core.commerce.commerce_trace import CommerceTraceTracker

log = logging.getLogger("helios.commerce.orchestrator")


class CommerceOrchestrator:
    """Master Orchestrator for HELIOS Natural-Language-to-Verified-Payment Commerce."""

    def __init__(self, transaction_bridge: Optional[CommerceTransactionBridge] = None) -> None:
        self.bridge = transaction_bridge or CommerceTransactionBridge()

    def process_commerce_request(self, user_prompt: str, mode: str = "live") -> Dict[str, Any]:
        commerce_id = f"comm_{uuid.uuid4().hex[:12]}"
        trace = CommerceTraceTracker(commerce_id)

        # 1. UNDERSTANDING
        intent = CommerceIntentClassifier.classify(user_prompt)
        trace.record_step("Intent Understanding", CommerceState.UNDERSTANDING.value, intent.to_dict())

        context = CommerceContext(commerce_id=commerce_id, intent=intent)
        self._last_context = context

        # If direct payment-only prompt (e.g., "pay ₹500")
        if intent.category == CommerceIntentCategory.PAYMENT_ONLY:
            amount_paise = int((intent.budget_limit_inr or 500.0) * 100)
            prep_res = self.bridge.adapter.execute_tool_call("prepare_payment", {
                "description": "Direct Payment",
                "amount": amount_paise,
                "merchant_name": "HELIOS Merchant"
            })
            context.state = CommerceState.REQUIRES_AUTHORIZATION
            context.intent_id = prep_res.get("data", {}).get("intent_id")
            trace.record_step("Direct Payment Prepared", CommerceState.REQUIRES_AUTHORIZATION.value, prep_res)
            return {
                "success": True,
                "commerce_id": commerce_id,
                "context": context.to_dict(),
                "payment_prepared": prep_res,
                "type": "PAYMENT_ONLY"
            }

        # 2. RESEARCHING
        candidates = CommerceResearcher.research(intent, mode=mode)
        context.candidates = candidates
        context.state = CommerceState.RESEARCHING
        trace.record_step("Product Research", CommerceState.RESEARCHING.value, {"count": len(candidates), "mode": mode})

        if not candidates:
            context.state = CommerceState.RESEARCH_FAILED
            context.error_message = "HELIOS couldn't retrieve reliable current prices from available sources."
            trace.record_step("Research Failed", CommerceState.RESEARCH_FAILED.value, {})
            return {
                "success": False,
                "commerce_id": commerce_id,
                "context": context.to_dict(),
                "error_message": context.error_message,
                "type": "RESEARCH_FAILED"
            }

        # 3. COMPARING
        comparison = CommerceComparator.compare(intent, candidates)
        context.comparison = comparison
        context.state = CommerceState.COMPARING
        trace.record_step("Candidate Comparison", CommerceState.COMPARING.value, comparison.to_dict())

        # 4. RECOMMENDING
        recommendation = CommerceRecommender.recommend(intent, comparison)
        context.recommendation = recommendation
        context.state = CommerceState.RECOMMENDING
        trace.record_step("Product Recommendation", CommerceState.RECOMMENDING.value, recommendation.to_dict() if recommendation else {})

        if not recommendation:
            context.state = CommerceState.RECOMMENDATION_FAILED
            context.error_message = "Failed to formulate explainable recommendation."
            return {"success": False, "commerce_id": commerce_id, "context": context.to_dict()}

        # Check if user requested information only or explicitly requested NO buy
        if intent.category == CommerceIntentCategory.INFORMATION_ONLY or intent.explicit_no_buy:
            context.state = CommerceState.COMPLETED
            trace.record_step("Informational Commerce Flow Completed", CommerceState.COMPLETED.value, {})
            return {
                "success": True,
                "commerce_id": commerce_id,
                "context": context.to_dict(),
                "type": "INFORMATION_ONLY"
            }

        # 5. DIRECT PRODUCT PAGE VERIFICATION FOR PURCHASE REQUESTS
        from core.commerce.product_verifier import ProductVerifier
        sel_cand = recommendation.selected_candidate
        verified_cand, ver_status = ProductVerifier.verify_candidate_url(sel_cand, intent.budget_limit_inr)
        context.recommendation.selected_candidate = verified_cand

        if not verified_cand.payment_eligible:
            context.state = CommerceState.VERIFICATION_FAILED
            context.error_message = (
                f"HELIOS found a possible match at {verified_cand.merchant} for ₹{verified_cand.price_inr:,.0f}, "
                f"but the merchant result is a search page rather than a directly verifiable product page. "
                f"I will not present it as a live verified price or prepare payment until the actual product page is verified."
            )
            trace.record_step("Direct Product Verification Failed", CommerceState.VERIFICATION_FAILED.value, {
                "url": verified_cand.source_url,
                "classification": verified_cand.classification,
                "reason": context.error_message
            })
            return {
                "success": False,
                "commerce_id": commerce_id,
                "context": context.to_dict(),
                "error_message": context.error_message,
                "type": "VERIFICATION_FAILED"
            }

        # 6. CALCULATING
        cost = CommerceCalculator.calculate(verified_cand)
        context.cost = cost
        context.state = CommerceState.CALCULATING
        trace.record_step("Cost Calculation", CommerceState.CALCULATING.value, cost.to_dict())

        # 7. TRANSACTION_PREPARED & AUTHORIZATION GUARD
        valid_auth, auth_msg = CommerceAuthorizationGuard.validate_authorization_request(context)
        if not valid_auth:
            context.state = CommerceState.TRANSACTION_FAILED
            context.error_message = auth_msg
            trace.record_step("Authorization Guard Blocked", CommerceState.TRANSACTION_FAILED.value, {"reason": auth_msg})
            return {"success": False, "commerce_id": commerce_id, "context": context.to_dict()}

        prep_res = self.bridge.prepare_transaction(intent, recommendation, cost)
        context.intent_id = prep_res.get("data", {}).get("intent_id")
        context.state = CommerceState.REQUIRES_AUTHORIZATION

        trace.record_step("Transaction Prepared", CommerceState.REQUIRES_AUTHORIZATION.value, prep_res)

        return {
            "success": True,
            "commerce_id": commerce_id,
            "context": context.to_dict(),
            "payment_prepared": prep_res,
            "type": "COMMERCE_TRANSACTION_READY"
        }
