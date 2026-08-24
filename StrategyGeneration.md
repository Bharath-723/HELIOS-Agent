# HELIOS v2: Strategy Generation & Planning Policies

This document specifies how candidate execution plans are generated using **Planning Policies** and task fingerprints.

---

## 1. Planning Policies
Alternative plan topologies are created by mapping the subtask list through five target planning policies:
- **Low-Resource**: Restricts local VRAM overhead, forces local `gemma3` model, limits retries to 1, and enables caching.
- **High-Accuracy**: Prioritizes local `mistral` or cloud `gemini` models, forces output schema verification tasks, and enables up to 5 execution retries.
- **Fast-Response**: Prioritizes cloud models, scales down latency estimates by 30%, and minimizes task dependencies.
- **Privacy-First**: Confines all processing to local models, strips external/online tools, and enforces local data sandboxes.
- **Parallel-First**: Removes optional dependencies to allow concurrent step execution.

---

## 2. Plan Fingerprints
Every generated plan candidate is assigned a deterministic **Plan Fingerprint**:
- Calculated as a `SHA-256` hash of the task list sequence containing task IDs, assigned models, tools, and dependency arrays.
- Enables topological equivalence checks across planning runs and fast structure lookup in planning memory.
