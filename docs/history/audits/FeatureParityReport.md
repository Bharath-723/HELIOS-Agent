# HELIOS CAHRA Feature Parity Report

---

### 1. Feature Coverage Matrix

| Intent Category | Supported Commands | Legacy Router Status | CAHRA Router Status | Parity Verified |
| :--- | :--- | :--- | :--- | :--- |
| **File Management** | `create_file`, `list_folder`, `find_file`, `convert_to_pdf` | Supported | **Supported** | **YES** |
| **System Controls** | `wifi_on`, `wifi_off`, `hotspot_on`, `hotspot_off`, `mute` | Supported | **Supported** | **YES** |
| **Notes Management** | `create_note`, `list_notes`, `read_note` | Supported | **Supported** | **YES** |
| **Task Scheduler** | `schedule_task`, `list_tasks`, `cancel_task` | Supported | **Supported** | **YES** |
| **Web Search** | `web_search`, `search_youtube` | Supported | **Supported** | **YES** |
| **General Chat** | `general_chat` | Supported | **Supported** | **YES** |

* **Feature removals**: **0**
* **Functionality changes**: **0** (CAHRA resolves candidate selections, and passes them to standard HybridLLM endpoints).
