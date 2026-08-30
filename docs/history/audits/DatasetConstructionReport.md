# HELIOS Benchmark Dataset Construction Report

---

### 1. Generation Methodology
The HELIOS evaluation corpus is constructed programmatically to guarantee 100% data integrity, schema compliance, and distribution balance:

* **Categories covered**: 15 distinct functional task vectors.
* **Prompt count**: 300 unique prompt entries (exactly 20 per category).
* **Ground truth labels**: Fully annotated with intent tags, expected parameters, optimal routes, model candidates, and resource levels.

---

### 2. Limitations & Extension Strategy
* **Keyword Dependency**: Prompts use templated index keys. Future runs will expand to user logs and colloquial phrasing variations.
