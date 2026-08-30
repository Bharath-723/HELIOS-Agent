# HELIOS — Payment Verification Specification

## Server-Side Verification Rules

1. **Client Parameter Untrust**:
   - The server does NOT trust any order ID, amount, or status parameter sent directly by client JS / browser callbacks.

2. **Trusted Order Matching**:
   - `PaymentVerifier` retrieves the original `PaymentIntent` from `PaymentRepository` using `intent_id`.
   - The order ID sent by the client must match `intent.metadata["order_id"]`.

3. **HMAC-SHA256 Signature Verification**:
   - Calculated signature string: `order_id + "|" + payment_id`.
   - HMAC hash is computed using `RAZORPAY_KEY_SECRET` with SHA256 digest.
   - Comparison uses `hmac.compare_digest()` for constant-time (timing-safe) string comparison.

4. **State Machine Finalization**:
   - Status transitions to `SIGNATURE_VERIFIED` and then `CAPTURED` only if verification passes.
   - Any signature mismatch immediately transitions transaction state to `VERIFICATION_FAILED`.
