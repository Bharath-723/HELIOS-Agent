# HELIOS — Auditable Commerce Execution Trace

## Trace Structure

`CommerceTraceTracker` maintains a transparent log of all 16 states:

```
Intent Understanding -> Product Research -> Candidate Comparison -> Recommendation Rationale -> Cost Calculation -> Transaction Preparation -> Human Authorization -> Razorpay Execution -> Signature Verification -> Memory Recording
```

Each step records step name, state, timestamp, and sanitized details.
