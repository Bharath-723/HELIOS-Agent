# HELIOS v2: Knowledge Architecture Specification

This document details the **Knowledge Plane Architecture** of HELIOS v2.

---

## 1. Architectural Overview
The Knowledge Plane is a backend-agnostic metadata layer decoupled from both execution engines and raw database configurations. It manages hierarchical memories, registry sources, and knowledge graphs to enable deterministic context assembly.

---

## 2. Entity Relation Graph
At the core of the knowledge layer is a deterministic **Knowledge Graph** mapping entities and directed relationships:
- Node representation: `KnowledgeGraphNode` (id, entity_type, properties).
- Edge representation: `KnowledgeGraphEdge` (source_id, target_id, relation_type, properties).
- Verification properties link edges back to their registered `KnowledgeSource` provenance, supporting full traceability and source reliability audits.
