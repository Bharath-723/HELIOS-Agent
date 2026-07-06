# HELIOS CAHRA Routing & Observability Audit Report

### 1. System Metadata
* **Algorithm Name**: CAHRA
* **Algorithm Version**: CAHRA-v1.0
* **Number of Candidate Models Profiles**: 4 candidate profiles

### 2. Stress Execution Profile (500 Iterations)
* **Total Prompts Executed**: 500
* **Average Routing Time**: 1.9785 ms
* **Max Routing Time**: 3.5963 ms
* **Average Routing Confidence**: 0.7027
* **Average Selection Margin**: 0.0905
* **Memory Leak footprint**: 0.0977 MB (Excellent memory safety)

### 3. Decision & Constraints Distribution
#### Route Decision Counts:
* **LOCAL Decisions**: 252 (50.4%)
* **CLOUD Decisions**: 248 (49.6%)

#### Preemptive Constraints Triggered:
* **check_local_model**: 208 times
* **check_connectivity**: 80 times
* **check_privacy**: 25 times
* **check_freshness**: 36 times
