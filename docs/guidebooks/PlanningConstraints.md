# HELIOS v2: Planning Constraints Specification

This document details the multi-level constraint classification model implemented in HELIOS v2.

---

## 1. Constraint Severity Classification
Constraints are categorized into four levels of severity:
1. **Forbidden**: Violation immediately invalidates the strategy (forces filter rejection).
2. **Discouraged**: Allowed if no other options exist, but incurs a planning penalty.
3. **Allowed**: Standard permissible behavior.
4. **Preferred**: Actively rewarded during evaluation.

---

## 2. Constraints Mapping

| Context Constraint | Task Action | Assigned Severity | Action on Strategy |
| :--- | :--- | :--- | :--- |
| **Offline State** | Task uses `WebSearch` | **Forbidden** | Filtered from candidates |
| **High Privacy** | Task uses Cloud Model | **Forbidden** | Filtered from candidates |
| **Medium Privacy** | Task uses Cloud Model | **Discouraged** | Utility penalty applied |
| **Low RAM Mode** | Task uses heavy local `mistral` | **Discouraged** | Utility penalty applied |
| **Offline State** | Task uses local tools | **Preferred** | High privacy score |
| **Low VRAM Mode** | Task uses local `gemma3` | **Allowed** | Metric remains normal |
