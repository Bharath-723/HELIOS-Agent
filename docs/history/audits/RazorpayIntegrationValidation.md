# HELIOS — Razorpay Integration Validation Report

## Validation Execution Summary

- **Suite 1: `razorpay_validation.py`**:
  - Total Tests: 20
  - Passed: 20
  - Failed: 0
  - Execution Time: 0.002 seconds
  - Coverage: Missing credentials, Sandbox config, Payment Intent creation, Invalid amount, Exceeded safety threshold, Authorization requirement, Unauthorized payment rejection, Idempotency duplicate detection, Order creation mock, Signature verification success & failure, Webhook signature success & failure, Webhook idempotency, Payment failure state, Successful payment state, Secret masking, Secret absence from string representations, Transaction state machine transitions.

- **Suite 2: `payment_security_validation.py`**:
  - Total Tests: 9
  - Passed: 9
  - Failed: 0
  - Execution Time: 0.001 seconds
  - Coverage: Key secret masking in repr/str, Key secret absence in `PaymentTrace`, Secret absence in UI payloads, LLM authorization blocking, Amount immutability post-authorization, Order ID substitution detection, Invalid webhook signature rejection, Duplicate webhook anti-replay, Payment preparation idempotency.

- **Regression Validation Suites**:
  - `reasoning_validation.py`: SUCCESS
  - `adaptive_planning_validation.py`: SUCCESS
  - `optimization_validation.py`: SUCCESS
  - `knowledge_validation.py`: SUCCESS
