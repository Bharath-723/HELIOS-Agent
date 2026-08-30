# HELIOS v2: Memory Hierarchy Design

This document describes the hierarchical memory design (L1 to L4) of HELIOS v2.

---

## 1. Layers Definitions
- **L1 Working Memory**: Direct prompt-reply dialogue lines. Access latency is minimized (~5ms).
- **L2 Session Memory**: Traces, intermediate graphs, and metadata generated within the current active session.
- **L3 Persistent Memory**: Local file notes, settings, and user parameters.
- **L4 Knowledge Memory**: Registered database nodes, external documentation files, and graph relationships.

---

## 2. Decoupled Architecture
- The hierarchy is completely backend-agnostic.
- Memory storage manages structures in unified `MemoryEntry` classes.
- Tag and metadata indexing are maintained separately, allowing future SQL/Vector backend integration without modifying indexing schemas.
