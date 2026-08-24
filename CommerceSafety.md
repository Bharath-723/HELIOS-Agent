# HELIOS — Commerce Safety & Risk Policies

## Hard Boundaries

1. **Zero LLM Autonomous Execution**: LLM cannot authorize payments or trigger order creation.
2. **Amount Immutability**: Post-authorization amount modification invalidates authorization.
3. **Threshold Enforcement**: Transactions > ₹10,000 require additional explicit authorization.
4. **Secret Masking**: Secrets are masked and excluded from logs, UI, and model contexts.
5. **Idempotency**: Duplicate payment preparations reuse original intent IDs to prevent double charges.
