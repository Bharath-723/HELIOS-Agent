# HELIOS — Razorpay Tool Capability Metadata

## Capability Definition

The `razorpay_payment` capability is registered in `core/payments/helios_payment_adapter.py` and exposed to the HELIOS tool router:

```json
{
  "name": "razorpay_payment",
  "category": "financial_transaction",
  "requires_authorization": true,
  "requires_network": true,
  "privacy_level": "sensitive",
  "execution_risk": "high",
  "local_execution": false,
  "cloud_execution": false
}
```

## Planner Constraints

1. `PAYMENT_REQUIRES_AUTHORIZATION`
2. `PAYMENT_REQUIRES_NETWORK`
3. `PAYMENT_REQUIRES_VERIFICATION`
4. `PAYMENT_CANNOT_BE_AUTONOMOUS`
5. `PAYMENT_AMOUNT_IMMUTABLE`
6. `PAYMENT_MERCHANT_IMMUTABLE`
7. `PAYMENT_IDEMPOTENT`
