# HELIOS — Human Authorization Policy Guard

## Hard Safety Boundary

`CommerceAuthorizationGuard` enforces strict human-in-the-loop authorization:
- **Mandatory Button Click**: `TransactionGuard` blocks `create_order` calls unless `user_authorized == True`.
- **Immutability Enforcement**: Item amount in paise and merchant references cannot be modified after authorization.
- **Safety Limits**: Transactions exceeding ₹10,000.00 require additional explicit authorization.
