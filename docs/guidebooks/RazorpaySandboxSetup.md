# HELIOS — Razorpay Sandbox & Environment Setup

## Environment Configuration

Place credentials in `.env` (never commit to Git):

```env
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
RAZORPAY_MODE=sandbox
MAX_PAYMENT_AMOUNT_INR=10000
```

## Template Setup

`.env.example` provides the safe repository template:

```env
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
RAZORPAY_MODE=sandbox
MAX_PAYMENT_AMOUNT_INR=10000
```

## Credential Availability & Fallback

If credentials are absent or invalid:
- `PaymentConfig.is_valid()` returns `False`.
- `PaymentConfig.get_status_message()` returns `"Payment capability unavailable: RAZORPAY_KEY_ID is missing."`.
- HELIOS agent remains fully operational and returns `"Payment capability unavailable"` without throwing unhandled exceptions.
