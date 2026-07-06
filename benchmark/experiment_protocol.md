# HELIOS Experimental Protocol

---

### 1. Hardware & System Specifications
* **CPU**: Multicore Processor (e.g. Intel Core i7 or equivalent).
* **RAM**: 8 GB minimum (to profile RAM capability drops below 4 GB).
* **Storage**: Solid State Drive (SSD) with at least 10 GB free space.

---

### 2. Software Specifications
* **OS**: Windows 10/11 (to access PowerShell and UI Automation API hooks).
* **Python**: Version 3.10.x.
* **Models**:
  * Local: `gemma3`, `mistral` (via Ollama).
  * Cloud: `gemini-2.0-flash` (Gemini API) and `gpt-4o-mini` (OpenAI API).

---

### 3. Execution Protocol
* **Warm-up Policy**: Run 5 initial dummy prompts prior to recording measurements to ensure model initialization and connection cache warming.
* **Repetition Strategy**: Every evaluation run must be repeated 3 times; report the average and standard deviation.
* **Threats to Validity**:
  * *Internal*: Fluctuating network latency on Cloud API calls (mitigated by separating routing latency from inference call latency).
  * *External*: Varying OS file system access permissions (mitigated by configuring test directories within sandbox workspaces).
