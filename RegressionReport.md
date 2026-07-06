# HELIOS CAHRA Production Regression Report

---

### 1. Verification of Intent Parsing
All functional workflows of HELIOS continue to operate with 100% parity after production integration of the CAHRA engine:

| Intent Category | Query Prompt | Routed Action | Parity Status |
| :--- | :--- | :--- | :--- |
| **Notes Manager** | *"create note about lunch menu"* | `create_note` | **PASS** |
| **File Creator** | *"find document.txt on desktop"* | `find_file` | **PASS** |
| **General Chat** | *"what is the weather in Delhi"* | `general_chat` | **PASS** |
| **YouTube Media** | *"play music on youtube"* | `search_youtube` | **PASS** |
| **Task Scheduler** | *"remind me in 5 minutes to stretch"* | `schedule_task` | **PASS** |

---

### 2. Regression Risk Assessment
* **Functional Coverage**: 100% of baseline command intents parse correctly.
* **Fallback Safety**: Tested and verified. In case of configuration file corruption or parser failure, the system falls back seamlessly to the legacy rules-based router.
