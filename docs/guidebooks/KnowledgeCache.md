# HELIOS v2: Knowledge Cache Specification

This document details the retrieval caching layer implemented in HELIOS v2.

---

## 1. Structure
The `KnowledgeCache` acts as a sub-millisecond cache for retrieved blocks:
- Keys are mapped directly from task query strings.
- Values store matching candidates list.
- TTL expiry prevents using outdated facts (e.g. 60 seconds limit).

---

## 2. Expiration and Stats
- Expirations are logged via `KnowledgeLogger`.
- Caching access counts are incremented and hit ratios are calculated to monitor efficiency.
