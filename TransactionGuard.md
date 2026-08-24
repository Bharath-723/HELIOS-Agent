# HELIOS — Transaction Guard Specification

## Overview

`TransactionGuard` (`core/payments/transaction_guard.py`) is the primary security boundary of HELIOS Payments. It enforces business rules and prevents autonomous financial execution.

## Policy Decision Matrix

| Operation | Guard Method | Required Policy Rules |
| :--- | :--- | :--- |
| **Order Creation** | `can_create_order(intent)` | 1. Intent exists & non-empty<br>2. Merchant name exists<br>3. Amount > 0 & Currency valid<br>4. Amount ≤ `MAX_PAYMENT_AMOUNT_INR` (₹10,000)<br>5. Explicit `user_authorized == True`<br>6. Status not already COMPLETED/CAPTURED |
| **Checkout Launch** | `can_open_checkout(intent, order)` | 1. Intent & Order exist<br>2. User authorized == True<br>3. Intent amount == Order amount<br>4. Status is not already COMPLETED |
| **Verification** | `can_verify_payment(intent, pid, oid)` | 1. Valid `payment_id` (`pay_...`) & `order_id` (`order_...`)<br>2. `order_id` matches trusted server intent metadata |
| **Completion** | `can_complete_transaction(intent, result)` | 1. Verification result `verified == True`<br>2. Verification result `success == True` |

## Transaction Decision Structure

```python
TransactionDecision(
    allowed=False,
    reason="Explicit user authorization required to proceed with payment",
    state=TransactionState.REQUIRES_AUTHORIZATION
)
```
