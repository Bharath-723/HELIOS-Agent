# HELIOS Evaluation Metrics Specification

---

### 1. Routing Metrics

#### Routing Accuracy (RA)
* **Purpose**: Measures correctness of LOCAL vs CLOUD routing decisions.
* **Formula**: 
  $$RA = \frac{N_{correct\_routes}}{N_{total\_runs}}$$
* **Unit**: Percentage (%)
* **Collection Method**: Logged against expected ground truth route parameters.

#### Confidence Score Error (CSE)
* **Purpose**: Gauges confidence estimation calibration.
* **Formula**:
  $$CSE = |Confidence_{predicted} - Confidence_{actual}|$$
* **Unit**: Normalized decimal (0.0 to 1.0)
* **Collection Method**: Parsed from decision snapshot metadata.

---

### 2. Intent Parsing Metrics

#### Intent Accuracy (IA)
* **Purpose**: Evaluates correctness of intent parsing.
* **Formula**:
  $$IA = \frac{N_{matching\_intents}}{N_{total\_runs}}$$
* **Unit**: Percentage (%)

---

### 3. Performance Metrics

#### Routing Latency (RL)
* **Purpose**: Quantifies processing overhead of CAHRA scoring.
* **Unit**: Milliseconds (ms)
* **Collection Method**: Timing values exported from `RoutingDiagnostics`.

---

### 4. Reliability Metrics

#### Offline Success Rate (OSR)
* **Purpose**: Validates offline operation constraints.
* **Formula**:
  $$OSR = \frac{N_{successful\_offline\_runs}}{N_{total\_offline\_requests}}$$
* **Unit**: Percentage (%)
