# HELIOS — Verified Commerce Memory Integration

## Persistent Memory Recorder

`CommerceMemoryRecorder` stores verified purchase summaries in HELIOS persistent memory (`L3_PERSISTENT`).

## Privacy & Security Guarantee

Stored entries exclude:
- Razorpay key secrets
- Webhook signatures
- Raw authentication tokens
- Financial payment credentials

Stored entries include:
- Purchased item name
- Merchant platform
- Verified amount in INR
- Timestamp and reference summary
