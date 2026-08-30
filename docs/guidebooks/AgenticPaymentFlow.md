# HELIOS — Agentic Payment Flow

## Step-by-Step Transaction Pipeline

1. **Intention & Preparation**:
   - Agent / User requests payment (e.g., *"Purchase subscription for ₹999"*).
   - `PaymentTool.prepare_payment()` creates `PaymentIntent` in state `REQUIRES_AUTHORIZATION`.

2. **Explicit Human Authorization (UI Card)**:
   - HELIOS presents an explicit authorization banner to the user:
     ```
     ----------------------------------
     TRANSACTION READY

     Merchant:  Example Merchant
     Item:      Example Product
     Amount:    ₹999.00

     Payment:   Razorpay (Sandbox)

     [ CANCEL ]       [ AUTHORIZE ]
     ----------------------------------
     ```
   - LLM cannot bypass this card or execute the transaction programmatically.

3. **User Action**:
   - User clicks `[ AUTHORIZE ]` -> `PaymentTool.authorize_payment()` transitions state to `AUTHORIZED`.

4. **Order Generation**:
   - `PaymentTool.create_authorized_order()` passes `TransactionGuard` checks and calls Razorpay POST `/v1/orders`.
   - `PaymentOrder` is stored server-side. State -> `ORDER_CREATED`.

5. **Checkout & Verification**:
   - Razorpay Checkout modal handles payment details.
   - Client sends callback (`payment_id`, `order_id`, `signature`) to server.
   - `PaymentVerifier` executes HMAC-SHA256 timing-safe signature check. State -> `CAPTURED`.
