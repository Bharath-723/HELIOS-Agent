# HELIOS — Sovereign Agentic AI Workbench

HELIOS is an on-premise, sovereign agentic AI workbench engineered for confidential industrial operations under **SIH Problem Statement 26117**. It combines open-weight local multimodal LLMs (Gemma 3, Mistral, Llama 3 via Ollama), on-device OCR (RapidOCR), lexical RAG document grounding, sandboxed Python code execution, spreadsheet analytics, and verifiable deliverable generation (DOCX, XLSX, PDF) within an application-enforced sovereign execution boundary.

---

## Table of Contents
1. [Problem Statement — SIH 26117](#problem-statement--sih-26117)
2. [What HELIOS Does](#what-helios-does)
3. [Core Architecture](#core-architecture)
4. [Feature Implementation Matrix](#feature-implementation-matrix)
5. [Sovereign Local-Only Architecture](#sovereign-local-only-architecture)
6. [CAHRA — Task-Aware Model Routing](#cahra--task-aware-model-routing)
7. [Agentic Execution Loop](#agentic-execution-loop)
8. [Multimodal Processing & On-Device OCR](#multimodal-processing--on-device-ocr)
9. [Local RAG / Industrial SOP Grounding](#local-rag--industrial-sop-grounding)
10. [Sandboxed Code Execution](#sandboxed-code-execution)
11. [Spreadsheet Analytics](#spreadsheet-analytics)
12. [Industrial Deliverables](#industrial-deliverables)
13. [Flagship Industrial Workflow (PSV-301 Relief Valve)](#flagship-industrial-workflow-psv-301-relief-valve)
14. [Additional Industrial Workflows](#additional-industrial-workflows)
15. [Network Security & Sovereignty](#network-security--sovereignty)
16. [Enterprise Authorization Model](#enterprise-authorization-model)
17. [Enterprise Data Continuity (Architecture Extension)](#enterprise-data-continuity-architecture-extension)
18. [Industrial Incident / Accident Data Continuity (Architecture Extension)](#industrial-incident--accident-data-continuity-architecture-extension)
19. [Deployment & Reference Hardware](#deployment--reference-hardware)
20. [Security Model](#security-model)
21. [Empirical Verification & Benchmark Results](#empirical-verification--benchmark-results)
22. [Technology Stack](#technology-stack)
23. [Repository Structure](#repository-structure)
24. [Installation & Setup](#installation--setup)
25. [Configuration](#configuration)
26. [Detailed Industrial Workflow Example](#detailed-industrial-workflow-example)
27. [Limitations & System Scope](#limitations--system-scope)
28. [License](#license)

---

## What HELIOS Does

HELIOS transforms natural-language requests into verified industrial deliverables through a strict agentic lifecycle:

```text
Natural-Language Request
        │
        ▼
Enterprise Authorization Gate (Role / Dept / Location)
        │
        ▼
Task Decomposition & CAHRA Model Routing
        │
        ▼
Local Tool Execution (OCR, Local RAG, Sandbox, Spreadsheet, File Creator)
        │
        ▼
Action Verification & Output Containment
        │
        ▼
Verifiable Deliverable Export (DOCX / XLSX / PDF)
```

---

## Core Architecture

The following diagram illustrates the complete HELIOS system architecture, showing the interaction between the UI layer, agent controller, routing engine, local tools, verification layer, artifact store, and enterprise continuity design.

```text
                               ┌─────────────────────────────────────────┐
                               │           User + Attachments            │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │     UI Layer (Glass Dock / Web App)     │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │      Enterprise Authorization Gate      │
                               │  (Role / Dept / Location / Permission)  │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │       HELIOS Agent Orchestrator         │
                               │        (agent.py / HELIOSAgent)         │
                               └───────────┬─────────────────┬───────────┘
                                           │                 │
                                           ▼                 ▼
                                   ┌──────────────┐   ┌─────────────┐
                                   │ CAHRA Router │   │    Task     │
                                   │  (v1 / v2)   │   │ Decomposer  │
                                   └───────┬──────┘   └─────────────┘
                                           │
                                           ▼
                               ┌─────────────────────────────────────────┐
                               │          Local Model Runtime            │
                               │  (Ollama / localhost:11434 / Open-Weight│
                               │   Models: gemma3, mistral, llama3)      │
                               └────────────────────┬────────────────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               │                               │
                    ▼                               ▼                               ▼
       ┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
       │   OCR & Vision Engine  │      │  Local RAG Grounding   │      │ Sandboxed Code Subproc │
       │ (RapidOCR / OpenCV)    │      │  (Lexical / 400-word)  │      │ (AST Check / Timeout)  │
       └────────────┬───────────┘      └────────────┬───────────┘      └────────────┬───────────┘
                    │                               │                               │
                    └───────────────────────────────┼───────────────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │  Spreadsheet & File Generation Engine   │
                               │   (Pandas / OpenPyXL / python-docx)     │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │  ActionVerifier & State Recovery Engine │
                               │     (Exit Codes / File Checksum)        │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │      ArtifactStore (Local FS Output)    │
                               │     └─ DOCX / XLSX / PDF Deliverables   │
                               └─────────────────────────────────────────┘

 ═════════════════════════════════════════════════════════════════════════════════════════════════
   SUPPORTING INFRASTRUCTURE:
   • Sovereign Network Audit: NetworkAuditMonitor (LOCAL_ONLY policy, JSONL telemetry)
   • Enterprise Continuity Layer (Architecture Extension): PostgreSQL + RLS + Storage (Backup/Recovery)
 ═════════════════════════════════════════════════════════════════════════════════════════════════
```

---


## Feature Implementation Matrix

To ensure absolute technical transparency, the table below clearly categorizes features into **VERIFIED / IMPLEMENTED**, **ARCHITECTURE EXTENSION**, and **FUTURE WORK**.

| Feature / Module | Status | Scope & Technical Implementation | Source Reference |
| :--- | :---: | :--- | :--- |
| **Local LLM Engine** | **VERIFIED** | Ollama local runner (`gemma3:4b`, `mistral:7b`, `llama3:8b`) via `localhost:11434`. | [`core/llm_engine.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/llm_engine.py) |
| **CAHRA Routing Engine** | **VERIFIED** | 5D utility evaluator ($R_p, R_f, R_c$, latency, cost) with empirical profiling store. | [`core/routing/`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/routing/) |
| **Sovereign Network Audit** | **VERIFIED** | Application-enforced `LOCAL_ONLY` egress guard with redacted JSONL audit log. | [`core/network_audit.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/network_audit.py) |
| **On-Device OCR & Vision** | **VERIFIED** | RapidOCR ONNX engine with 4 OpenCV image pre-processing variants. | [`core/ocr_provider.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/ocr_provider.py) |
| **Local Lexical RAG** | **VERIFIED** | 400-word sliding window chunker with 50-word overlap & lexical keyword scoring. | [`core/local_rag.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/local_rag.py) |
| **Sandboxed Code Execution** | **VERIFIED** | Bounded Python subprocess with AST import screening, secret scrubbing, and 5s timeout. | [`core/code_sandbox.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/code_sandbox.py) |
| **Spreadsheet Analytics** | **VERIFIED** | Pandas + OpenPyXL engine for CSV/XLSX metrics, failure rates, and summary export. | [`modules/spreadsheet_agent.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/modules/spreadsheet_agent.py) |
| **Document Deliverables** | **VERIFIED** | Automated Word (`.docx`) Plant Approval Notes & PDF generation (`ReportLab`). | [`modules/file_creator.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/modules/file_creator.py) |
| **Action Verification** | **VERIFIED** | Post-execution verification of process exit codes, window states, and file artifacts. | [`core/action_verifier.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/action_verifier.py) |
| **Flagship Inspection Workflow** | **VERIFIED** | End-to-end 5-step PSV-301 inspection report processing & approval note generation. | [`core/task_decomposer.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/task_decomposer.py) |
| **Enterprise Data Continuity** | **EXTENSION** | Supabase PostgreSQL + RLS + Storage architecture for encrypted backup/recovery. | Architecture Specification |
| **Incident / Accident Schema** | **EXTENSION** | Role/location-restricted industrial incident & safety audit record schema design. | Architecture Specification |
| **Dense Vector Embedding RAG** | **FUTURE WORK** | On-device vector store (e.g. Chroma/FAISS) with local embedding models. | Planned Capability |
| **Automated PPTX Export** | **FUTURE WORK** | Template-driven PowerPoint presentation builder for executive reporting. | Planned Capability |

---

## Sovereign Local-Only Architecture

HELIOS enforces a strict sovereign boundary for confidential industrial environments:

1. **On-Premise LLM Inference**: All AI model reasoning is executed locally via Ollama on `http://localhost:11434`. No external API calls are dispatched during sovereign execution.
2. **On-Device OCR & Document Processing**: Scanned PDF inspection reports and images are processed locally using RapidOCR (ONNX runtime) and OpenCV.
3. **Local Knowledge Base (RAG)**: SOP manuals and engineering guidelines are indexed and searched strictly on local disk.
4. **Isolated Code Sandbox**: Python analysis scripts run in a bounded subprocess with AST safety screening and zero network access.
5. **Application-Enforced Egress Guard**: The `NetworkAuditMonitor` intercepts request attempts. In `LOCAL_ONLY` mode, non-localhost outbound requests are **blocked before execution**.
6. **Redacted Audit Telemetry**: Execution telemetry, routing decisions, policy enforcement, and model latencies are logged to `data/audit/network_audit.jsonl` with automatic credential scrubbing.

> **Precise Sovereign Positioning**:
> - Application-enforced local-only execution is verified.
> - **0 external requests were executed in the verified local-mode test suite**.
> - Localhost Ollama communication (`http://localhost:11434`) is permitted for open-weight model inference.
> - Cloud AI is not the inference engine in sovereign mode.

---

## CAHRA — Task-Aware Model Routing

The **Context Aware Hybrid Routing Algorithm (CAHRA)** dynamically selects the optimal open-weight model for each request based on capability requirements and hardware constraints.

### 1. Routing Mechanics
- **Eligible Model Filtering**: Scans active local models (`gemma3`, `mistral`, `llama3`) and filters candidates matching task constraints.
- **Capability Constraints**: Evaluates system RAM and VRAM availability. Applies a -30% complexity penalty for low system RAM (<4GB available) and a -40% latency penalty for CPU-only execution.
- **Task-Aware Selection**: Evaluates incoming intent against task archetypes (`industrial_workflow`, `code_execution`, `document_analysis`, `general_chat`).
- **Weighted Utility Scoring**: Computes a multi-dimensional utility score:
  $$U = w_p \cdot R_p + w_f \cdot R_f + w_c \cdot R_c + w_l \cdot S_{\text{latency}} + w_k \cdot S_{\text{cost}}$$
  where $R_p$ is Privacy Score, $R_f$ is Freshness Score, $R_c$ is Complexity Score, $S_{\text{latency}}$ is estimated response time, and $S_{\text{cost}}$ is token expenditure score.
- **Candidate Fallback**: If a primary model fails to respond or is resource-constrained, CAHRA seamlessly falls back to lighter open-weight candidates (e.g. `gemma3:4b`).

> **Note**: CAHRA optimizes task allocation across registered open-weight models based on empirical benchmarks; it is not claimed to be universally superior to every model under all conditions.

---

## Agentic Execution Loop

HELIOS executes user requests using a structured, state-driven agent loop:

```text
   ┌──────────┐
   │ OBSERVE  │ ──► Inspects prompt, attached documents, and OS window state
   └────┬─────┘
        ▼
   ┌──────────┐
   │   PLAN   │ ──► Decomposes task into ordered steps via TaskDecomposer
   └────┬─────┘
        ▼
   ┌──────────┐
   │ EXECUTE  │ ──► Dispatches actions to local tools (OCR, RAG, Sandbox, FileCreator)
   └────┬─────┘
        ▼
   ┌──────────┐
   │  VERIFY  │ ──► ActionVerifier checks exit code, stdout, and deliverable existence
   └────┬─────┘
        ├──► Verified: Export artifact to ArtifactStore
        └──► Unverified:
               ├──► Action Retry: RecoveryEngine executes 1 bounded retry attempt
               └──► Human Escalation: Transition state to WAITING_FOR_USER
```

### Distinction Between Agent Recovery & Model Fallback
- **Agent Recovery (`RecoveryEngine`)**: Action-level self-repair when a local tool or file generation step fails validation (e.g. retrying code sandbox execution with adjusted parameters).
- **CAHRA Model Fallback**: Infrastructure-level re-routing when an LLM connection times out or encounters resource constraints, switching candidate models.

---

## Multimodal Processing & On-Device OCR

HELIOS processes visual and scanned industrial inputs through an on-device pipeline:

- **Supported Inputs**: Scanned PDF inspection reports, technical schematics, equipment photographs, and printed/handwritten maintenance logs.
- **RapidOCR Engine**: Uses ONNX runtime models for fast text detection and recognition without external cloud API calls.
- **OpenCV Pipeline**: Generates 4 localized image pre-processing variants to maximize text extraction accuracy:
  1. Grayscale Conversion & Contrast Normalization
  2. Binarization / Thresholding
  3. Image Upscaling & Noise Reduction
  4. CLAHE (Contrast Limited Adaptive Histogram Equalization)
- **Visual Desktop Observation**: The `ScreenObserver` captures active desktop state on demand, enumerating Win32 Z-order windows while explicitly excluding the HELIOS UI overlay from visual inspection.

---

## Local RAG / Industrial SOP Grounding

HELIOS grounds AI reasoning directly in local plant Standard Operating Procedures (SOPs):

- **Lexical Retrieval Engine**: Indexes `.docx`, `.pdf`, `.txt`, and `.md` files stored in `data/` or attached by the user.
- **Chunking Strategy**: 400-word sliding windows with a 50-word overlap between consecutive chunks.
- **Keyword Scoring**: Computes match relevance based on term frequency and document position overlap.
- **Provenance & Citations**: Extracted facts are attached to `ResponseSource` objects, ensuring generated deliverables cite exact file names and section headings.

> **Technical Clarification**: Current HELIOS implementation uses a fast, lightweight **lexical keyword RAG baseline** on local disk. Dense vector embedding search is classified as a future architecture extension.

---

## Sandboxed Code Execution

For numerical calculations, data transformations, and custom script execution, HELIOS uses an isolated Python sandbox ([`core/code_sandbox.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/code_sandbox.py)):

- **AST Safety Screening**: Inspects script Abstract Syntax Trees prior to execution. Rejects prohibited modules (`os.system`, `subprocess`, `shutil`, `socket`, `eval`, `exec`).
- **Secret Scrubbing**: Scrubs sensitive environment variables and API keys from the subprocess environment before execution.
- **Execution Boundary**:
  - Timeout: Strict **5.0-second** execution cap.
  - Subprocess Isolation: Runs in a dedicated background worker.
  - Capture & Verification: Captures `stdout`, `stderr`, and `exit_code`. `ActionVerifier` confirms success before passing output to deliverables.

---

## Spreadsheet Analytics

The `SpreadsheetAgent` ([`modules/spreadsheet_agent.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/modules/spreadsheet_agent.py)) provides automated spreadsheet processing:

- **Ingestion**: Reads `.csv` and `.xlsx` files into Pandas DataFrames.
- **Header Classification & Cleaning**: Automatically identifies column data types, handles missing values, and parses timestamps.
- **Metrics Computation**: Calculates key operational metrics, unit failure rates, mean operating pressures, and threshold violations.
- **Summary Workbook Generation**: Produces formatted Excel (`.xlsx`) workbooks complete with summary headers using OpenPyXL.

---

## Industrial Deliverables

HELIOS generates verified, production-ready deliverables saved directly to `data/output/`:

- **Word Documents (`.docx`)**: Formatted Plant Approval Notes, Inspection Executive Summaries, and Emergency Memos using `python-docx`.
- **Excel Workbooks (`.xlsx`)**: Inspection metric summaries and unit defect analysis workbooks using `openpyxl`.
- **PDF Documents (`.pdf`)**: Formatted document exports built via ReportLab.

---

## Flagship Industrial Workflow (PSV-301 Relief Valve)

The flagship demonstration scenario validates the full HELIOS capability chain on a Pressure Safety Valve (PSV-301) inspection:

```text
[Step 1: Scanned Report]  ──► Scanned inspection report image (scanned_inspection_report.png)
                                 │
                                 ▼
[Step 2: RapidOCR Engine] ──► Extracts text: "Inspected Component: Valve PSV-301 | Measured Pressure: 450 PSI"
                                 │
                                 ▼
[Step 3: Local RAG]       ──► Retrieves SOP_Plant_Safety_2026.docx: "Max allowable pressure for PSV-301 = 400 PSI"
                                 │
                                 ▼
[Step 4: Reasoning & SB]  ──► CAHRA routes to local LLM; Code Sandbox calculates 12.5% over-pressure delta
                                 │
                                 ▼
[Step 5: ActionVerifier]  ──► Generates Plant_Approval_Note_PSV301.docx & verifies file integrity
                                 │
                                 ▼
[Deliverable Export]      ──► Verified Word document exported to data/output/
```

*(Note: PSV-301 inspection metrics represent synthetic demonstration data used for SIH 26117 verification testing).*

---

## Additional Industrial Workflows

1. **Analytical Coding Workflow**:
   - User inputs a complex mathematical or data processing prompt.
   - HELIOS generates Python script -> AST safety screen -> Sandboxed execution -> Returns verified numerical result.
2. **Spreadsheet Inspection Analytics**:
   - User uploads `inspection_metrics.csv`.
   - `SpreadsheetAgent` analyzes failure rates -> Generates `inspection_metrics_summary.xlsx`.
3. **Multimodal Local Knowledge Task**:
   - User uploads a handwritten maintenance note alongside a machinery manual.
   - RapidOCR extracts text -> Local RAG matches manual recommendations -> Local LLM outputs combined action plan.
4. **Document Generation Workflow**:
   - User requests a formal summary of local SOP updates.
   - Local LLM synthesizes notes -> `file_creator.py` generates formatted `.docx` and `.pdf` deliverables.

---

## Network Security & Sovereignty

HELIOS provides explicit, audit-verifiable network security controls ([`core/network_audit.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/core/network_audit.py)):

- **`LOCAL_ONLY` Policy Enforcement**: When sovereign mode is enabled, outbound network requests to external domains are intercepted and blocked prior to socket creation.
- **Localhost Exception**: Communication with local services (`http://localhost:11434` for Ollama) is explicitly permitted.
- **Audit Logging**: Every routing decision, tool execution, and network check is logged to `data/audit/network_audit.jsonl`.
- **Empirical Evidence**: In the automated compliance test suite (`tests/test_sovereign_network_policy.py`), **0 external network requests were executed**.

```json
{
  "timestamp": "2026-10-03T15:59:54Z",
  "policy": "LOCAL_ONLY",
  "action": "BLOCKED_BEFORE_REQUEST",
  "target": "external_live_data",
  "reason": "LOCAL_ONLY_POLICY",
  "network_call_executed": false,
  "bytes_transferred": 0
}
```

---

## Enterprise Authorization Model

HELIOS includes a server-side authorization gate design to prevent unauthorized tool execution:

```text
Authenticated User
       │
       ▼
   Role Check ──► (e.g. Safety Engineer)
       │
       ▼
Department Check ──► (e.g. Safety Department)
       │
       ▼
Location Boundary ──► (e.g. Hyderabad Plant)  [HARD DATA BOUNDARY]
       │
       ▼
Permission Level ──► (e.g. READ / EXECUTE)
       │
       ▼
  Tool Action ──► ALLOW or DENY
```

### Authorization Rules
- **Non-LLM Controlled**: Authorization decisions are enforced by hard-coded policy gates, not by LLM prompts.
- **Hard Location Boundary**: Cross-location resource access (e.g. a Hyderabad user requesting Chennai plant data) is **DENY by default**.
- **Untrusted Client Location**: Location claims supplied in client headers are strictly untrusted and validated against backend session credentials.

> *Example*:
> - `Safety Engineer + Safety + Hyderabad + READ` -> Access to Hyderabad Safety SOP: **ALLOW**
> - `Safety Engineer + Safety + Chennai + READ` -> Access to Hyderabad Safety SOP: **DENY**

*(Note: Plant roles and location schemas serve as illustrative access control models in the engineering prototype).*

---

## Enterprise Data Continuity (Architecture Extension)

For enterprise deployments requiring disaster recovery and multi-device state synchronization without compromising LLM inference privacy:

```text
Local HELIOS Environment
       │
       ├─ 1. Classify Document (PUBLIC / INTERNAL / CONFIDENTIAL / HIGHLY_SENSITIVE)
       ├─ 2. Validate User Authorization & Location Access
       ├─ 3. Generate SHA-256 Checksum & Version Tag
       │
       ▼
Approved Backup Pipeline (Policy-Controlled)
       │
       ▼
Enterprise Data Continuity Layer (Supabase PostgreSQL + RLS + Encrypted Storage)
       │
       ▼
Authorized Disaster Recovery ──► Restores data to local HELIOS for local LLM processing
```

### Key Principles
- **Separation of Inference & Continuity**: Supabase serves as a controlled enterprise data-continuity layer. **Supabase is NOT the LLM inference engine**. Local AI inference remains 100% on-premise.
- **Policy-Controlled Backup**: Files classified as `HIGHLY_SENSITIVE` remain local-only and are excluded from cloud continuity.
- **No Automatic Uploads**: HELIOS does not automatically upload local workspace files.
- **Server-Side Credentials**: Service-role keys remain strictly server-side.

---

## Industrial Incident / Accident Data Continuity (Architecture Extension)

- **Planned Capability**: Enterprise continuity schema for industrial incident and accident records.
- **Security Scope**: Incident logs are classified as `CONFIDENTIAL` or `HIGHLY_SENSITIVE`, requiring multi-factor role authorization, location-based Row Level Security, and encrypted payload storage.
- **Status Notice**: **Architecture Extension / Planned Enterprise Capability — not yet a deployed module in the current baseline codebase.**

---

## Deployment & Reference Hardware

| Environment | CPU Cores | System RAM | GPU VRAM | Storage | Model Capability |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Prototype Reference** *(Engineering Baseline)* | 4 – 8 Cores | 16 – 32 GB | 6 – 12 GB *(RTX 3060/4060)* | 250 GB+ SSD | Runs `gemma3:4b` & `mistral:7b` locally via Ollama. |
| **Production Scale** *(Enterprise Deployment)* | 8 – 16+ Cores | 32 – 64+ GB | 12 – 24+ GB *(RTX 4090/A4000)* | 1 TB+ NVMe | Concurrent local inference (`llama3:8b`/`mistral:7b`) + local OCR. |

*(Note: Actual hardware requirements scale with model parameter size, context window length, request concurrency, and document volume).*

---

## Security Model

HELIOS implements a layered security defense model:
1. **Local-Only Boundary**: Application-enforced egress blocking in sovereign mode.
2. **Sandbox Subprocess**: Python AST inspection, secret scrubbing, and 5s execution caps.
3. **Output Containment**: Verification of exit codes and stdout before deliverable export.
4. **Deterministic Authorization**: Non-LLM role, department, and location policy checks.
5. **Audit Logging**: Redacted JSONL log of all system actions (`data/audit/network_audit.jsonl`).
6. **Credential Protection**: Environment variables scrubbed before code execution; service keys protected.

---

## Empirical Verification & Benchmark Results

The HELIOS implementation has been rigorously validated across multiple empirical test suites:

### 1. SIH 26117 Automated Acceptance Suite (`tests/sih_26117_compliance_validation.py`)
- **Result**: **19 / 19 Requirements PASSED (100.0% Compliance)**.
- Validated: Secret scrubbing, open-weight models, CAHRA routing, persistent session, sandboxed code execution, local tool suite, RapidOCR, deliverable creation (DOCX/XLSX), local RAG grounding, flagship inspection workflow, sovereign network audit, and spreadsheet processing.

### 2. Sovereign Network Policy Test (`tests/test_sovereign_network_policy.py`)
- **Result**: **12 / 12 Tests PASSED**.
- Confirmed: **0 external requests executed during sovereign mode execution**.

### 3. Controlled 30-Task Coding Evaluation
Evaluated across a controlled 30-task coding benchmark comparing local models and CAHRA routing versions:

| Model / Routing Configuration | Tasks Completed | Pass Rate | Adaptive Fallback Behavior |
| :--- | :---: | :---: | :--- |
| **Mistral 7B** (Direct) | 29 / 30 | 96.7% | N/A |
| **Gemma 3 4B** (Direct) | 30 / 30 | 100.0% | N/A |
| **CAHRA v1** | 30 / 30 | 100.0% | Static routing |
| **CAHRA v2** (No Fallback) | 29 / 30 | 96.7% | Fallback disabled |
| **CAHRA v2** (With Adaptive Fallback) | 30 / 30 | 100.0% | Recovered 1 unique-success task via adaptive candidate fallback |

*(Note: Evaluated on a controlled 30-task benchmark; routing overhead measurements are distinct from LLM inference latency).*

---

## Technology Stack

- **Core Logic & Orchestration**: Python 3.10+, PyWin32, APScheduler.
- **Local Model Engine**: Ollama (`gemma3`, `mistral`, `llama3`).
- **OCR & Computer Vision**: RapidOCR (ONNX runtime), OpenCV.
- **Data & Analytics**: Pandas, OpenPyXL.
- **Deliverable Generators**: `python-docx` (Word), ReportLab (PDF), OpenPyXL (Excel).
- **Web Interface**: Next.js 16, React 19, Tailwind CSS.
- **Desktop UI**: Custom PyQt / Tkinter floating glass dock.
- **Enterprise Continuity Architecture**: Supabase PostgreSQL, Row Level Security (RLS), Storage.

---

## Repository Structure

```text
HELIOS_FINAL/
├── app/                        # Next.js 16 Web Application pages & styles
│   ├── globals.css             # Design tokens, variables & glassmorphism CSS
│   ├── layout.tsx              # Application layout container
│   └── page.tsx                # Main workbench page router
├── components/                 # React UI Components
│   ├── ChatWorkspace.tsx       # Live chat & streaming response renderer
│   ├── FeatureCards.tsx        # Quick capability feature cards
│   ├── Header.tsx              # Glass header & mode indicator
│   ├── InputSection.tsx        # Command input section & action chips
│   ├── NavigationRail.tsx      # Sidebar navigation rail
│   └── RightSidebar.tsx        # System health & model status panel
├── core/                       # Core decision, routing, and security engines
│   ├── routing/                # CAHRA routing engine, score engine & capability matrix
│   ├── action_verifier.py      # Desktop action & execution verifier
│   ├── code_sandbox.py         # Isolated Python execution sandbox
│   ├── execution_state.py      # Execution event state & telemetry model
│   ├── llm_engine.py           # Local Ollama & cloud LLM connectors
│   ├── local_rag.py            # Lexical local document RAG connector
│   ├── network_audit.py        # Sovereign network policy & JSONL auditor
│   ├── ocr_provider.py         # On-device RapidOCR & OpenCV image pipeline
│   └── task_decomposer.py      # 5-step industrial task planner
├── modules/                    # Capability modules
│   ├── desktop_agent.py        # OS application control & file operations
│   ├── document_processor.py   # Document text extraction & PDF generation
│   ├── file_creator.py         # Automated DOCX Plant Approval Note builder
│   ├── spreadsheet_agent.py    # Excel & CSV analytics engine
│   └── voice_input.py          # Speech-to-text STT listener
├── data/                       # Local datasets, SOPs & output store
│   ├── audit/                  # Sovereign network audit JSONL logs
│   ├── diagnostics/            # CAHRA routing diagnostics JSON snapshots
│   ├── output/                 # Generated deliverables (DOCX, XLSX, PDF)
│   └── SOP_Plant_Safety_2026.docx # Sample industrial safety SOP
├── docs/                       # Technical documentation & guidebooks
│   └── guidebooks/             # SIH 26117 architecture, metrics & traceability reports
├── tests/                      # Automated test suite
│   ├── sih_26117_compliance_validation.py # 19-point SIH acceptance suite
│   ├── test_cahra_v2.py        # CAHRA v2 routing engine tests
│   ├── test_response_ux_integration.py   # Response UX & model identity tests
│   └── test_sovereign_network_policy.py  # Sovereign network audit tests
├── agent.py                    # HELIOSAgent Orchestrator controller
├── helios_api.py               # FastAPI backend server for Web UI
├── helios_popup.py             # Custom desktop UI application setup
├── main.py                     # CLI entry point
├── package.json                # Next.js web application manifest
├── requirements.txt            # Python dependency manifest
└── README.md                   # Technical source of truth
```

---

## Installation & Setup

### Prerequisites
- **Operating System**: Windows 10 / 11 (64-bit)
- **Python**: Python 3.10+
- **Node.js**: Node.js 18+ (for Web UI)
- **Local Model Runner**: [Ollama](https://ollama.com/) with `gemma3` model (`ollama pull gemma3`)

### 1. Clone & Setup Python Environment
```bash
git clone https://github.com/Bharath-723/HELIOS-Agent.git
cd HELIOS-Agent

python -m venv venv
.\venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure Environment
```bash
copy .env.example .env
```
Ensure `SOVEREIGN_MODE=true` and `OLLAMA_BASE_URL=http://localhost:11434` for local-only execution.

### 3. Launch Backend API Server
```bash
python helios_api.py
```
*(Runs on `http://127.0.0.1:8000`).*

### 4. Launch Next.js Web UI
In a separate terminal:
```bash
npm install
npm run dev
```
*(Open `http://localhost:3000` in your browser).*

### 5. Launch CLI / Desktop Dock
```bash
python main.py
```

---

## Configuration

Key environment settings in `.env`:

| Variable | Mode | Description | Default |
| :--- | :---: | :--- | :--- |
| `SOVEREIGN_MODE` | `LOCAL_ONLY` | Forces local execution; blocks external cloud requests. | `true` |
| `OLLAMA_BASE_URL` | `LOCAL_ONLY` | Ollama local API endpoint. | `http://localhost:11434` |
| `OLLAMA_MODEL` | `LOCAL_ONLY` | Default local open-weight LLM. | `gemma3` |
| `LLM_MODE` | Hybrid | Model routing mode (`auto`, `offline`, `online`). | `auto` |
| `CLOUD_PROVIDER` | Optional | Cloud LLM provider (`gemini`, `openrouter`). | `gemini` |
| `GEMINI_API_KEY` | Optional | API key for Gemini (disabled in Sovereign mode). | `your_key_here` |
| `SUPABASE_URL` | Continuity | Supabase project URL (Enterprise Backup Layer). | `https://xyz.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Continuity | Server-side service key for encrypted backup. | `your_service_key` |

---

## Detailed Industrial Workflow Example

**Scenario**: A refinery safety engineer inspects Relief Valve PSV-301 and uploads the scanned report image (`scanned_inspection_report.png`).

1. **User Command**:
   > *"Analyze the attached PSV-301 inspection report and prepare an approval note using the applicable local SOP."*
2. **On-Device OCR**: RapidOCR extracts: `Inspected Component: Valve PSV-301 | Measured Pressure: 450 PSI`.
3. **Local RAG Grounding**: `LocalRAGConnector` searches `SOP_Plant_Safety_2026.docx` and retrieves: `Section 4.2: Relief valve PSV-301 maximum operating pressure limit is 400 PSI`.
4. **CAHRA Routing & Reasoning**: CAHRA selects `gemma3` locally. The LLM identifies that 450 PSI exceeds the 400 PSI safety threshold by 50 PSI (12.5%).
5. **Sandboxed Calculation**: `CodeSandbox` executes:
   ```python
   observed = 450
   limit = 400
   delta_pct = ((observed - limit) / limit) * 100
   print(f"OVER_PRESSURE: {delta_pct:.2f}%")
   ```
   *Output*: `OVER_PRESSURE: 12.50%` (Exit Code 0).
6. **Action Verification & Deliverable Creation**: `ActionVerifier` validates output. `file_creator.py` generates `Plant_Approval_Note_PSV301.docx` containing formal findings, SOP citations, and recommended maintenance actions.
7. **Artifact Export**: Delivered to `data/output/Plant_Approval_Note_PSV301.docx`.

---

## Limitations & System Scope

- **Industrial Safety Boundary**: HELIOS is an AI decision-support workbench; it does not replace certified plant safety engineers or formal human sign-off procedures.
- **OCR & Vision Scope**: RapidOCR text extraction accuracy depends on scan resolution, contrast, and font clarity.
- **Lexical RAG Scope**: Current retrieval uses a fast lexical keyword matching baseline; dense vector embeddings are classified as an architecture extension.
- **Voice Input Scope**: Speech-to-text relies on Windows speech APIs with known background noise caveats.
- **Enterprise Continuity**: Supabase integration represents an enterprise data-continuity architecture specification, not an active cloud LLM inference engine.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
