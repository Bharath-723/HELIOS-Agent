# HELIOS — Payment State Integration

## Backend to UI State Mapping

| TransactionState | User-Facing UI Label | UI Action / Visual Representation |
| :--- | :--- | :--- |
| `CREATED` | Transaction created | Internal intent recorded in repository |
| `REQUIRES_AUTHORIZATION` | Awaiting your explicit authorization | Transaction Review Card rendered with `[ Authorize ]` button |
| `AUTHORIZED` | Authorized — preparing order | Buttons disabled; initiating Razorpay Order API |
| `ORDER_CREATED` | Razorpay order created | Server order ID generated |
| `CHECKOUT_OPEN` | Payment window open | Razorpay checkout active |
| `PAYMENT_RECEIVED` | Payment received — verifying... | Client callback received, initiating HMAC check |
| `SIGNATURE_VERIFIED` | Signature verified | Timing-safe HMAC check passed |
| `CAPTURED` | Payment completed & verified | Green Verified Result Card rendered in chat |
| `FAILED` | Payment failed | Red Error Card rendered with failure reason |
| `CANCELLED` | Cancelled by user | Card status updated to Cancelled |
| `VERIFICATION_FAILED` | Payment verification failed | Red Error Card: "No funds marked complete" |
| `REQUIRES_ADDITIONAL_AUTHORIZATION` | Safety threshold exceeded | Blocked by safety limit (₹10,000 max) |
