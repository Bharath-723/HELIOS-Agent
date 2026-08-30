# HELIOS v2: Retrieval Engine Specification

This document specifies the pipeline and algorithms coordinated by the `RetrievalEngine` in HELIOS v2.

---

## 1. Pipeline Order
Retrieval executes through the following stages:

```
[Retrieval Planning] ──► [Memory Search] ──► [Knowledge Search]
                                                    │
[Retrieval Context] ◄── [Validation] ◄── [Ranking] ◄── [Evidence Collection]
```

---

## 2. Evidence Collection & Ranking
- Gathered matching records are wrapped as `EvidenceBlock` entries.
- Blocks are scored and sorted according to:
  
  $$\text{Rank Score} = (\text{Relevance Score} \times 0.8) + (\text{Source Reliability} \times 0.2)$$
  
- Ensures that facts sourced from verified registries rise to Rank 1 over unverified files.
- The `ContextAssembler` merges the top ranked blocks into the final context payload.
