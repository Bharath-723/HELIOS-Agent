# HELIOS — Payment Intent Planning

## Cognitive Intent Classification

HELIOS strictly separates commercial intent into two categories:

1. **Payment Execution Requests** (Triggers `razorpay_payment`):
   - `"pay ₹500"`
   - `"buy this course for ₹999"`
   - `"purchase this item"`
   - `"make the payment"`
   - `"checkout"`
   - `"complete my purchase"`

2. **Informational / History Requests** (Triggers `general_chat` or history view):
   - `"What is the price of this?"` -> Informational
   - `"How much did I pay?"` -> History query
   - `"Show my previous payments"` -> Payment history view
   - `"Prepare the payment but don't execute it"` -> Preparation only (`REQUIRES_AUTHORIZATION`)

## Step-by-Step Cognitive Execution Plan

```mermaid
graph TD
    Step1[1. Parse Prompt & Extract Amount / Merchant] --> Step2[2. Validate Amount Limits ≤ ₹10,000]
    Step2 --> Step3[3. Create PaymentContext & PaymentIntent]
    Step3 --> Step4[4. Set Status: REQUIRES_AUTHORIZATION]
    Step4 --> Step5[5. Present Transaction Review UI Card to User]
    Step5 --> Step6[6. Wait for Explicit User Button Click]
    Step6 -->|Authorize| Step7[7. Create Razorpay Server Order]
    Step6 -->|Cancel| Step8[8. Transition State to CANCELLED]
    Step7 --> Step9[9. Verify HMAC-SHA256 Signature]
    Step9 --> Step10[10. Render Verified Result Card]
```
