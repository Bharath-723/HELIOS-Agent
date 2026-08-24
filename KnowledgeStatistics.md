# HELIOS v2: Knowledge Statistics Specification

This document details the telemetry metrics compiled by the `KnowledgeStatisticsCompiler` in HELIOS v2.

---

## 1. Metrics Tracked
- **Hit Ratio**: Ratio of cache hits to total cache lookups.
- **Average Latency**: Average time in milliseconds to resolve retrieval queries.
- **Average Retrieval Depth**: Average number of evidence blocks retrieved.
- **Memory Distribution**: Count of records stored across L1, L2, L3, and L4 memory layers.
- **Memory Utilization**: Estimated total memory footprint in bytes.

---

## 2. Telemetry and Logging
- Telemetry details are logged in JSON format.
- Exposed to diagnostics dashboards to monitor retrieval performance and cache optimization effectiveness.
