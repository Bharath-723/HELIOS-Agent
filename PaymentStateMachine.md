# HELIOS — Payment State Machine

## TransactionState Enum Values

- `CREATED`: Intent registered in repository.
- `REQUIRES_AUTHORIZATION`: Intent prepared, awaiting explicit human approval.
- `AUTHORIZED`: Human user confirmed transaction.
- `ORDER_CREATED`: Razorpay server-side Order created.
- `CHECKOUT_OPEN`: Checkout modal active on client.
- `PAYMENT_RECEIVED`: Raw client callback received.
- `SIGNATURE_VERIFIED`: HMAC-SHA256 signature verified by server.
- `CAPTURED`: Payment captured successfully.
- `FAILED`: Order creation or processing failed.
- `CANCELLED`: User declined transaction authorization.
- `VERIFICATION_FAILED`: HMAC signature check or order mismatch failed.
- `REQUIRES_ADDITIONAL_AUTHORIZATION`: Amount exceeds configured safety threshold (₹10,000).

## State Transition Workflow

```mermaid
stateDiagram-v2
    [*] --> CREATED
    CREATED --> REQUIRES_AUTHORIZATION
    REQUIRES_AUTHORIZATION --> AUTHORIZED : User Authorizes
    REQUIRES_AUTHORIZATION --> CANCELLED : User Declines
    REQUIRES_AUTHORIZATION --> REQUIRES_ADDITIONAL_AUTHORIZATION : Exceeds Max Limit
    AUTHORIZED --> ORDER_CREATED : Server Order API
    ORDER_CREATED --> CHECKOUT_OPEN : Launch Checkout
    CHECKOUT_OPEN --> PAYMENT_RECEIVED : Callback Received
    PAYMENT_RECEIVED --> SIGNATURE_VERIFIED : HMAC Verify OK
    PAYMENT_RECEIVED --> VERIFICATION_FAILED : HMAC Verify Fail
    SIGNATURE_VERIFIED --> CAPTURED : Complete Payment
    CAPTURED --> [*]
```
