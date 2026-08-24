# HELIOS v2: Resource Optimizer Specification

This document details the local model standardization and cache optimization rules implemented in HELIOS v2.

---

## 1. Local Model Standardization
Loading different local LLMs (e.g., `gemma3` and `mistral`) sequentially causes VRAM loading overhead and thrashing. The `ResourceOptimizer` standardizes models to minimize loading cycles:
- **Rule**: If the plan uses multiple different local models, standardise on the stronger model (e.g. substitute `gemma3` with `mistral` if `mistral` is already required in the plan).
- Eliminates model loading/unloading cycles.

---

## 2. Cache Optimization
The optimizer inspects task tools and descriptions to maximize cache reuse:
- Read-only actions (such as `WebSearch` lookups or `NotesManager` reads) are explicitly flagged with `cacheable = True` to enable structure and result caching across agent sessions.
