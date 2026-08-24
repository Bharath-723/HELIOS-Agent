# HELIOS — Agentic Payment Security Audit

## Hard Security Proof Matrix

| Attack Vector / Security Requirement | Defense Mechanism | Proof of Compliance |
| :--- | :--- | :--- |
| **LLM Autonomous Payment Execution** | `TransactionGuard.can_create_order()` strictly checks `user_authorized == True`. | `test_05` & `test_sec_04` confirm LLM execution calls are rejected. |
| **Razorpay Secret Leakage** | `PaymentConfig` masks secret strings. `PaymentTraceTracker` redacts sensitive keys. | `test_18`, `test_sec_01`, `test_sec_02` prove 0 secrets in logs or UI. |
| **Amount Modification Post-Authorization** | Intent amount stored as integer paise. Guard rejects order creation if amount is altered. | `test_08` & `test_sec_05` prove amount immutability. |
| **Client Order ID Substitution** | Server matches client order ID against trusted `intent.metadata["order_id"]`. | `test_17` & `test_sec_06` confirm substitution attacks are blocked. |
| **Invalid Webhook Injection** | `PaymentVerifier` validates `X-Razorpay-Signature` HMAC. | `test_14` & `test_sec_07` confirm invalid webhooks are rejected with HTTP 400. |
| **Duplicate Webhook Anti-Replay** | `PaymentRepository` tracks processed `account_id` + `created_at` event IDs. | `test_15` & `test_sec_08` prove replay calls return `status: ignored`. |
| **Safety Transaction Cap** | `MAX_PAYMENT_AMOUNT_INR` (₹10,000 max) blocks large unauthorized charges. | `test_10` confirms threshold enforcement. |
