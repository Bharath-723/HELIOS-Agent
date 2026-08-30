# HELIOS v2: Memory Architecture Specification

This document specifies the hierarchical storage and indexing layout implemented in HELIOS v2.

---

## 1. Storage Layers
Memory is organized into four hierarchical levels to mirror cognitive processing:
- **L1 Working Memory**: Holds current prompt transactions, active execution steps, and transient context parameters.
- **L2 Session Memory**: Persists conversation history logs and execution trace history of the active session.
- **L3 Persistent Memory**: Houses user preference definitions and notes files.
- **L4 Knowledge Memory**: Manages crawled indexes, database nodes, and registered document references.

---

## 2. Inverted Indexing
To prevent expensive text scanning, memory additions are registered in the `MemoryIndex`:
- **Tag Index**: Direct lookup of entry IDs matching search tags.
- **Metadata Index**: Key-value mapping pointing metadata properties (e.g. `source_id`, `version`) to matching records.
- Guarantees sub-millisecond retrieval of indexed records.
