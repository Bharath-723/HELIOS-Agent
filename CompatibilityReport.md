# HELIOS CAHRA Compatibility Report

---

### 1. Backward Compatibility Verification
The integrated routing package is fully backward compatible with the baseline HELIOS configuration settings:

* **`.env` Properties Supported**:
  * `OLLAMA_BASE_URL` & `OLLAMA_MODEL` (Mapped to CandidateManager capability checks).
  * `GEMINI_API_KEY` & `OPENAI_API_KEY` (Parsed to confirm cloud model availability).
  * `CLOUD_PROVIDER` (Determines the default cloud candidate model name).
* **Legacy Fallback Path**: If CAHRA initialization fails or throws an exception during execution, control falls back instantly to the old `_use_cloud` intent router, avoiding any service interruption.
* **Hardware Integration**: Runs natively on Windows 10/11 using standard `psutil` handles without requiring administrative overrides.
