# HELIOS — Post-Payment Transaction Verification

## Signature Verification Specification

`CommerceVerifier` validates payment integrity post-checkout:
- Matches trusted server order ID against client payload.
- Validates signature using timing-safe comparison:

```python
hmac.compare_digest(calculated_signature, client_signature)
```

- Blocks verification if order ID substitution or invalid signature is detected.
