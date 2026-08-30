# HELIOS — Product Research Subsystem

## Overview

`CommerceResearcher` gathers candidate options matching target item descriptions and user-defined constraints.

## Candidate Structure

Each discovered candidate contains:
- `name`: Verified product title
- `description`: Product summary
- `price_inr`: Exact price in INR
- `merchant`: Verified merchant platform (e.g. Amazon India, Flipkart, Myntra)
- `rating`: Customer satisfaction score (1.0 to 5.0)
- `review_count`: Verified review count
- `features`: Key product attributes
- `pros` & `cons`: Balance of strengths and limitations
- `constraints_satisfied`: List of satisfied user criteria
- `confidence`: Data freshness and reliability score
