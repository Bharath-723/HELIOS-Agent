# HELIOS — Commercial Intent Understanding

## Intent Classification Categories

HELIOS classifies commercial natural language prompts into four distinct categories:

1. **INFORMATION_ONLY**:
   - Prompts: `"What is the best keyboard under ₹2000?"`, `"Find me something under ₹1000 but don't buy anything"`
   - Flow: Research -> Compare -> Recommend -> STOP (No payment transaction card is rendered).

2. **PURCHASE_PREPARATION**:
   - Prompts: `"Find the best keyboard under ₹2000 and prepare the purchase"`
   - Flow: Research -> Compare -> Recommend -> Calculate -> Prepare Transaction (`REQUIRES_AUTHORIZATION`).

3. **PURCHASE_REQUEST**:
   - Prompts: `"Find me a keyboard under ₹2000 and buy the best one"`
   - Flow: Research -> Compare -> Recommend -> Calculate -> Prepare Transaction -> Render Transaction Review UI Card -> Await User Authorization.

4. **PAYMENT_ONLY**:
   - Prompts: `"Pay ₹500"`
   - Flow: Direct payment intent preparation -> Render Transaction Review UI Card.
