"""
core/payments/helios_payment_adapter.py — HELIOS Agentic Payment Adapter
==========================================================================
Isolated adapter interface for HELIOS planning/tool execution.
Allows HELIOS cognitive planning to express 'razorpay_payment' intents without disturbing frozen reasoning core.
"""

import logging
from typing import Dict, Any, Optional
from core.payments.payment_tool import PaymentTool
from core.payments.payment_config import PaymentConfig

log = logging.getLogger("helios.payments.adapter")


class HeliosPaymentAdapter:
    """
    Adapter pattern exposing 'razorpay_payment' tool signature to HELIOS tool execution registry.
    """
    def __init__(self, config: Optional[PaymentConfig] = None) -> None:
        self.config = config or PaymentConfig()
        self.tool = PaymentTool(self.config)

    def execute_tool_call(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translates HELIOS tool invocations into safe payment operations.
        Example action: 'prepare_payment', 'create_order', 'get_status'
        """
        log.info("HeliosPaymentAdapter: Executing action '%s'", action)

        if action in ("prepare_payment", "razorpay_payment", "pay"):
            desc = params.get("description", "HELIOS Order")
            amt = int(params.get("amount", 0))
            curr = params.get("currency", "INR")
            merchant = params.get("merchant_name", "HELIOS Merchant")
            ref = params.get("merchant_reference", "")
            return self.tool.prepare_payment(desc, amt, curr, merchant, ref, metadata=params)

        elif action in ("authorize_payment", "user_authorize"):
            intent_id = params.get("intent_id", "")
            confirm = bool(params.get("user_confirm", True))
            return self.tool.authorize_payment(intent_id, confirm)

        elif action in ("create_order", "create_authorized_order"):
            intent_id = params.get("intent_id", "")
            mock = bool(params.get("mock", False))
            return self.tool.create_authorized_order(intent_id, mock=mock)

        elif action in ("verify_payment", "verify_signature"):
            intent_id = params.get("intent_id", "")
            pid = params.get("payment_id", "")
            oid = params.get("order_id", "")
            sig = params.get("signature", "")
            return self.tool.verify_payment(intent_id, pid, oid, sig)

        elif action in ("get_status", "payment_status"):
            intent_id = params.get("intent_id", "")
            return self.tool.get_payment_status(intent_id)

        elif action in ("cancel_payment", "cancel"):
            intent_id = params.get("intent_id", "")
            reason = params.get("reason", "Cancelled via agent")
            return self.tool.cancel_payment(intent_id, reason)

        return {
            "success": False,
            "message": f"Unsupported payment action '{action}'",
            "data": None
        }
