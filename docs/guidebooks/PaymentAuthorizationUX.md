# HELIOS — Payment Authorization UX Specification

## Transaction Review UI Card Architecture

When a transaction enters `REQUIRES_AUTHORIZATION`, HELIOS renders a glass surface card inside `ui/chat_view.py`:

```
──────────────────────────────────────────────────
💳 PAYMENT READY                 Razorpay Sandbox

Merchant:    Example Store
Item:        AI Engineering Course
Amount:      ₹999.00
Reason:      Matches your request
Status:      Awaiting your explicit authorization

[ ❌ Cancel ]   [ 💳 Authorize Payment ]
──────────────────────────────────────────────────
```

## Visual Design Principles

- **Glass Surface**: Translucent background (`C.GLASS_3`) with warm gold / cyan perimeter highlight (`C.GOLD` / `#F59E0B`).
- **Semantic Icon**: Financial card icon (`💳`).
- **Typography Hierarchy**: Prominent bold font for amount in INR (`₹999.00`).
- **Control Locking**: Immediate button disabling (`state="disabled"`) on click to prevent double-clicking or re-submission.
- **State Transition Feedback**: Dynamic label updating from `"Awaiting your explicit authorization"` to `"Authorized — preparing Razorpay Order..."` or `"Cancelled by user"`.
