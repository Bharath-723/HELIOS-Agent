# HELIOS — Webhook Architecture

## Webhook Handling Flow

```mermaid
sequenceDiagram
    participant RZP as Razorpay Server
    participant WH as Webhook Endpoint (POST /webhooks/razorpay)
    participant Verifier as PaymentVerifier
    participant Repo as PaymentRepository

    RZP->>WH: POST Webhook Event Payload + X-Razorpay-Signature
    WH->>Verifier: Validate HMAC Signature (RAZORPAY_WEBHOOK_SECRET)
    alt Signature Invalid
        Verifier-->>WH: Raise PaymentVerificationException
        WH-->>RZP: HTTP 400 Bad Request
    else Signature Valid
        Verifier->>Repo: Idempotency Check (account_id + created_at)
        alt Duplicate Event
            Repo-->>WH: Event already processed
            WH-->>RZP: HTTP 200 (status: ignored)
        else New Event
            Repo->>Repo: Store Event ID & Update State
            WH-->>RZP: HTTP 200 OK (Immediate Response)
        end
    end
```

## Supported Events

1. `payment.captured`: Payment received and captured by Razorpay.
2. `payment.failed`: Payment attempt failed at gateway.
3. `order.paid`: Order completely fulfilled.

## Anti-Replay & Idempotency

- `PaymentRepository.record_webhook_event()` maintains processed event IDs.
- Duplicate webhook calls with identical event timestamps and account IDs are acknowledged with HTTP 200 (`status: ignored`) without reprocessing.
