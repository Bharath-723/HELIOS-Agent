# HELIOS — Payment Security Architecture

## Zero Secret Exposure Guarantee

`RAZORPAY_KEY_SECRET` and `RAZORPAY_WEBHOOK_SECRET` are protected by multi-layered isolation:

1. **No LLM / UI Exposure**:
   - Secrets are loaded exclusively from environment variables via `PaymentConfig`.
   - `PaymentConfig.__repr__` and `__str__` mask all secret strings (e.g. `rzp_***456`).
   - `PaymentTraceTracker` and `sanitize_payload()` automatically redact keys containing `secret`, `signature`, `auth`, or `password`.
   - Secrets never enter local model context, prompts, logs, UI payloads, or benchmark data.

2. **Amount Immutability**:
   - Amounts are handled strictly as integer values in the smallest currency unit (paise for INR).
   - Once a `PaymentIntent` is prepared and authorized, `TransactionGuard` blocks any attempt to modify the server-side order amount.

3. **Client Order ID Substitution Protection**:
   - `TransactionGuard` cross-checks client-supplied order IDs against trusted server intent records before permitting verification.

4. **Timing-Safe HMAC-SHA256 Verification**:
   - Signature checks use `hmac.compare_digest()` to prevent timing side-channel attacks.

5. **Human-in-the-Loop Explicit Authorization**:
   - The LLM can prepare a payment intent (`REQUIRES_AUTHORIZATION`), but CANNOT execute order creation or payment authorization independently.
