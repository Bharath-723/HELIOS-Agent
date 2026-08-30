"""
core/commerce/commerce_transaction.py — Razorpay Payment Subsystem Bridge
===========================================================================
Interfaces the Commerce layer with core/payments/ (HeliosPaymentAdapter, PaymentTool,
TransactionGuard, PaymentVerifier). Reuses Phase 1 implementation directly.
"""

import logging
from typing import Dict, Any, Optional
from core.payments import HeliosPaymentAdapter, PaymentConfig, TransactionState
from core.commerce.commerce_models import RecommendationResult, CostBreakdown, CommerceIntent

log = logging.getLogger("helios.commerce.transaction")


class CommerceTransactionBridge:
    """Bridge connecting Commerce Orchestrator to core/payments Subsystem."""

    def __init__(self, payment_adapter: Optional[HeliosPaymentAdapter] = None) -> None:
        self.adapter = payment_adapter or HeliosPaymentAdapter()

    def prepare_transaction(
        self,
        intent: CommerceIntent,
        recommendation: RecommendationResult,
        cost: CostBreakdown
    ) -> Dict[str, Any]:
        log.info("CommerceTransactionBridge: Preparing transaction for '%s' (Amount: %d paise)",
                 recommendation.selected_candidate.name, cost.total_paise)

        res = self.adapter.execute_tool_call("prepare_payment", {
            "description": recommendation.selected_candidate.name,
            "amount": cost.total_paise,
            "currency": cost.currency,
            "merchant_name": recommendation.selected_candidate.merchant,
            "merchant_reference": f"comm_ref_{recommendation.selected_candidate.candidate_id}",
            "metadata": {
                "quantity": cost.quantity,
                "unit_price_inr": cost.unit_price_inr or (cost.item_price_inr / max(1, cost.quantity)),
                "reason": recommendation.reason,
                "source_url": recommendation.selected_candidate.source_url,
                "candidate_id": recommendation.selected_candidate.candidate_id,
            }
        })

        return res

    def authorize_transaction(self, intent_id: str, user_confirm: bool = True) -> Dict[str, Any]:
        log.info("CommerceTransactionBridge: Authorizing intent '%s' (User confirm: %s)", intent_id, user_confirm)
        return self.adapter.execute_tool_call("authorize_payment", {
            "intent_id": intent_id,
            "user_confirm": user_confirm
        })

    def create_order(self, intent_id: str, mock: bool = True) -> Dict[str, Any]:
        return self.adapter.execute_tool_call("create_order", {
            "intent_id": intent_id,
            "mock": mock
        })

    def verify_payment(
        self,
        intent_id: str,
        payment_id: str,
        order_id: str,
        signature: str
    ) -> Dict[str, Any]:
        return self.adapter.execute_tool_call("verify_payment", {
            "intent_id": intent_id,
            "payment_id": payment_id,
            "order_id": order_id,
            "signature": signature
        })

    def cancel_transaction(self, intent_id: str, reason: str = "Cancelled by user") -> Dict[str, Any]:
        return self.adapter.execute_tool_call("cancel_payment", {
            "intent_id": intent_id,
            "reason": reason
        })
