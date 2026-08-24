"""
core/payments/payment_repository.py — Transaction Repository & Idempotency Storage
====================================================================================
Isolated repository pattern for PaymentIntents, Orders, Results, and Webhooks.
Supports idempotency key resolution to prevent duplicate order generation.
"""

import threading
import logging
from typing import Dict, Optional, List
from core.payments.payment_models import PaymentIntent, PaymentOrder, PaymentResult, TransactionState

log = logging.getLogger("helios.payments.repository")


class PaymentRepository:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._intents: Dict[str, PaymentIntent] = {}
        self._orders: Dict[str, PaymentOrder] = {}
        self._results: Dict[str, PaymentResult] = {}
        self._processed_webhook_events: Dict[str, str] = {}  # event_id -> processed_at

    def save_intent(self, intent: PaymentIntent) -> None:
        with self._lock:
            self._intents[intent.intent_id] = intent
            log.debug("Repository: Saved intent '%s' [%s]", intent.intent_id, intent.status.value)

    def get_intent(self, intent_id: str) -> Optional[PaymentIntent]:
        with self._lock:
            return self._intents.get(intent_id)

    def find_idempotent_intent(self, merchant_name: str, merchant_ref: str, amount: int) -> Optional[PaymentIntent]:
        """
        Finds existing intent with identical merchant_reference or identical (merchant_name, amount, merchant_reference)
        to prevent duplicate order creation.
        """
        with self._lock:
            if not merchant_ref:
                return None
            for intent in self._intents.values():
                if intent.merchant_reference and intent.merchant_reference == merchant_ref:
                    return intent
                if (intent.merchant_name == merchant_name and
                        intent.merchant_reference == merchant_ref and
                        intent.amount == amount):
                    return intent
            return None

    def save_order(self, intent_id: str, order: PaymentOrder) -> None:
        with self._lock:
            self._orders[order.order_id] = order
            intent = self._intents.get(intent_id)
            if intent:
                intent.status = TransactionState.ORDER_CREATED
                intent.metadata["order_id"] = order.order_id
            log.debug("Repository: Linked Order '%s' to Intent '%s'", order.order_id, intent_id)

    def get_order(self, order_id: str) -> Optional[PaymentOrder]:
        with self._lock:
            return self._orders.get(order_id)

    def save_result(self, intent_id: str, result: PaymentResult) -> None:
        with self._lock:
            self._results[intent_id] = result
            intent = self._intents.get(intent_id)
            if intent:
                intent.status = result.status
            log.debug("Repository: Saved PaymentResult for Intent '%s' [Success=%s]", intent_id, result.success)

    def get_result(self, intent_id: str) -> Optional[PaymentResult]:
        with self._lock:
            return self._results.get(intent_id)

    def record_webhook_event(self, event_id: str, timestamp: str) -> bool:
        """
        Returns True if event is NEW and recorded. Returns False if duplicate.
        """
        with self._lock:
            if event_id in self._processed_webhook_events:
                return False
            self._processed_webhook_events[event_id] = timestamp
            return True

    def clear(self) -> None:
        with self._lock:
            self._intents.clear()
            self._orders.clear()
            self._results.clear()
            self._processed_webhook_events.clear()
