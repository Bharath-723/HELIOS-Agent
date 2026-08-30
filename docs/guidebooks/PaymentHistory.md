# HELIOS — Payment History Integration

## Overview

HELIOS provides a lightweight payment history view built on top of `PaymentRepository`.

## Displayed Attributes

- **Merchant Name**: (e.g. Udemy, HELIOS Store)
- **Amount**: Formatted in INR (`₹999.00`)
- **Timestamp**: Date and time of payment intent creation
- **Transaction Status**: `CAPTURED`, `AUTHORIZED`, `CANCELLED`, `VERIFICATION_FAILED`
- **Masked Payment ID**: `pay_••••1234`
- **HMAC Verification State**: Verified / Unverified

## Security & Privacy Rules

1. Secrets (`key_secret`, `webhook_secret`) are NEVER retrieved or stored in history entries.
2. Complete raw payment signatures are masked.
3. Users can copy the masked payment reference ID for support receipts.
