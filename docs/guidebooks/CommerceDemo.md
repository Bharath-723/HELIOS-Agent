# HELIOS — Razorpay Buildathon Demonstration Guide

## Demo Scenarios

### Scenario 1: Full End-to-End Agentic Commerce
Prompt: `"Find me a good wireless keyboard under ₹2,000 and buy the best one."`
- Demonstrates: Intent -> Research -> Compare -> Recommend -> Cost -> Transaction Card -> Authorize -> Razorpay Sandbox Order -> Verify -> Memory.

### Scenario 2: Direct Payment Request
Prompt: `"Pay ₹500 to test the payment flow."`
- Demonstrates: Intent -> Transaction Review Card -> Authorize -> Razorpay Sandbox Order -> Verify.

### Scenario 3: Informational Research Request
Prompt: `"Find me something useful under ₹1,000 but don't buy anything."`
- Demonstrates: Intent -> Research -> Compare -> Recommend -> STOP (Proves HELIOS respects user intent and does NOT open payment authorization).
