# HELIOS v2: Knowledge Manager Specification

This document specifies the registry features of the `KnowledgeManager` in HELIOS v2.

---

## 1. Registry Attributes
External documents and database files are registered under the registry mapping:
- `source_id`: Unique identifier.
- `reliability_score`: Float value representing authority (e.g. 1.0 for verified documents, 0.5 for untrusted nodes).
- `verification_status`: Status enum (`verified`, `unverified`, `suspicious`).
- `freshness_status`: Evaluated status enum (`fresh`, `stale`, `expired`).

---

## 2. Freshness Checks
- The manager updates freshness status by checking `last_modified` age against configurable thresholds in `knowledge_rules.json`.
- Automatically marks records stale or expired to prevent outdated cache access.
