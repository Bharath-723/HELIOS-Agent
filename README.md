# HELIOS

HELIOS is an autonomous desktop AI agent that connects natural-language user requests to local or cloud AI models and practical operating tools. It unifies document processing, desktop automation, visual screen observation, web search, spreadsheet analytics, sandboxed code execution, and safe commerce research while applying strict explicit authorization boundaries where actions have side effects.

---

## HELIOS in Action

The following screenshots demonstrate HELIOS executing real tasks through its desktop interface, including natural-language interaction, model routing, Screen Context, desktop actions, and verification.

### 1. HELIOS Desktop Interface

![HELIOS Desktop Interface](docs/images/helios-main-interface.png)
<!-- Screenshot to be added -->

*HELIOS desktop interface showing the floating glass dock, model selector, Screen Context control, chat view, and runtime status bar.*

---

### 2. Natural-Language Task Execution

![Natural-Language Task Execution](docs/images/helios-task-execution.png)
<!-- Screenshot to be added -->

*A real HELIOS request being interpreted, routed, and executed through the Orchestrator.*

---

### 3. CAHRA Routing in Real Time

![CAHRA Routing in Real Time](docs/images/helios-cahra-routing.png)
<!-- Screenshot to be added -->

*Real-time CAHRA routing diagnostics showing the selected model, extracted context features, scoring breakdown, and routing decision.*

---

### 4. Screen Context

![Screen Context](docs/images/helios-screen-context.png)
<!-- Screenshot to be added -->

*HELIOS using Screen Context to observe the current desktop state on demand for a screen-dependent request.*

---

### 5. Live Desktop Interaction

![Live Desktop Interaction](docs/images/helios-live-desktop-interaction.png)
<!-- Screenshot to be added -->

*HELIOS interacting with a user application through the desktop session workflow.*

---

### 6. Verification Before Response

![Verification State](docs/images/helios-verification.png)
<!-- Screenshot to be added -->

*HELIOS evaluating post-execution window state via the StateVerifier before delivering a response.*

---

### 7. Commerce & Payment Verification

![Commerce Verification](docs/images/helios-commerce-verification.png)
<!-- Screenshot to be added -->

*HELIOS verifying a product page and preparing a payment intent card requiring explicit user authorization.*

---

## Table of Contents
1. [What HELIOS Is](#what-helios-is)
2. [What HELIOS Can Do](#what-helios-can-do)
3. [How HELIOS Works](#how-helios-works)
4. [The HELIOS Orchestrator](#the-helios-orchestrator)
5. [Natural-Language Intent](#natural-language-intent)
6. [CAHRA — Context Aware Hybrid Routing Algorithm](#cahra--context-aware-hybrid-routing-algorithm)
7. [How CAHRA Chooses a Model](#how-cahra-chooses-a-model)
8. [Local and Cloud Models](#local-and-cloud-models)
9. [Screen Context & Live Desktop Interaction](#screen-context--live-desktop-interaction)
10. [Desktop Automation](#desktop-automation)
11. [Verification Before Response](#verification-before-response)
12. [Documents, Files and RAG](#documents-files-and-rag)
13. [Web Search](#web-search)
14. [Voice Input](#voice-input)
15. [Notes and Reminders](#notes-and-reminders)
16. [System Controls](#system-controls)
17. [Commerce](#commerce)
18. [Payment and Payment Security](#payment-and-payment-security)
19. [Privacy](#privacy)
20. [Architecture](#architecture)
21. [Project Structure](#project-structure)
22. [Installation](#installation)
23. [Configuration](#configuration)
24. [Usage Examples](#usage-examples)
25. [Limitations](#limitations)
26. [License](#license)

---

## What HELIOS Is

HELIOS is a desktop-native AI assistant designed to eliminate the friction between human intent and software execution. Instead of requiring users to learn CLI commands, navigate nested settings menus, or switch between multiple single-purpose tools, HELIOS interprets natural language, resolves what capability is required, routes the request to an appropriate local or cloud AI model, executes the task, verifies the outcome, and presents a grounded response.

---

## What HELIOS Can Do

| Capability | Scope & Processing | Key Operations | Read / Action |
|---|---|---|:---:|
| **Natural Language Interaction** | Local / Cloud | Converts freeform English requests into structured actions or conversational answers | Read |
| **CAHRA Model Routing** | System Engine | Dynamically routes between local Ollama models (`gemma3`, `mistral`) and cloud LLMs (`gemini-3.6-flash`, `gpt-4o-mini`, `openrouter`) | Read |
| **Screen Observation** | Demand-Driven Local | Captures desktop screenshot on demand, enumerates Win32 Z-order windows, extracts text via RapidOCR, and grounds reasoning | Read |
| **Desktop Automation** | Native Local API | Opens applications (`Chrome`, `Settings`, `Notepad`, `Calculator`), closes browser tabs (`Ctrl+W`), minimizes windows (`Win+Down`), and controls system settings | Action |
| **Browser & Web Tasks** | Web / Local | Opens web URLs, conducts web searches via Tavily & DuckDuckGo API, and reads web content | Action |
| **Document Processing & Conversion** | Local File System | Extracts text from PDF, DOCX, TXT, MD, and converts documents to PDF using ReportLab | Read / Action |
| **Local RAG Retrieval** | Local Storage | Searches local notes and index entries to answer questions grounded in local knowledge | Read |
| **Spreadsheet Processing** | Local File System | Ingests `.xlsx` and `.csv` files, filters rows, aggregates columns, and calculates metrics | Read |
| **Sandboxed Code Execution** | Isolated Process | Runs generated Python code in a sandboxed subprocess with strict execution timeouts | Action |
| **Commerce Research** | Web API | Searches multiple online platforms (Amazon, Flipkart, etc.), compares prices, and verifies direct product pages | Read |
| **Payment Preparation & Security** | Sandbox / API Boundary | Generates Razorpay payment previews with HMAC signatures and requires explicit user authorization before order creation | Action |

---

## How HELIOS Works

HELIOS processes user requests through a two-tier pipeline consisting of deterministic pre-routing guards, semantic intent parsing, capability-aware model routing, isolated capability execution, and state verification.

```text
    ┌──────────────────────────────┐
    │        User / Voice         │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │        HELIOS UI / CLI       │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │     HELIOSAgent Orchestrator │
    │                              │
    │ Guards • Context • State     │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │          NLRouter            │
    │   Understand user intent     │
    └──────────────┬───────────────┘
                   │
          ┌────────┴─────────┐
          │                  │
          ▼                  ▼
    ┌─────────────┐    ┌──────────────┐
    │   CAHRA     │    │ Tool / Action│
    │ Model Route │    │   Modules    │
    └──────┬──────┘    └──────┬───────┘
           │                  │
           ▼                  │
    ┌─────────────┐            │
    │ HybridLLM   │            │
    └──────┬──────┘            │
           └──────────┬────────┘
                      ▼
              ┌──────────────┐
              │   Execute    │
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │   Observe    │
              │ + Verify     │
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │   Response   │
              └──────────────┘
```

---

## The HELIOS Orchestrator

The **Orchestrator** (implemented in [`agent.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/agent.py) as `HELIOSAgent`) is the central controller of the system.

When a user submits a prompt, the Orchestrator manages the request lifecycle:

1. **Pre-Routing Safety Guards**:
   - **Guard 0.58 (Desktop Session)**: Checks active desktop automation sessions and screen privacy policies.
   - **Guard 0.6 (Commerce & Payments)**: Intercepts shopping, pricing, and payment requests, delegating them to `CommerceOrchestrator` before general chat routing.
2. **Intent Resolution (`NLRouter`)**: Maps natural-language inputs to specific actions or general conversation.
3. **Capability Dispatch**: Selects the required module (`DesktopSessionManager`, `DocumentProcessor`, `OCRProvider`, `LocalRAGConnector`, `CodeSandbox`, `CommerceOrchestrator`, `SpreadsheetAgent`).
4. **CAHRA Model Routing**: Selects the appropriate local or cloud AI model for reasoning.
5. **Execution Verification (`ActionVerifier`)**: Compares post-execution window states to verify action success.
6. **Response Generation**: Formats grounded markdown cards and sanitizes model output for UI rendering.

### Concrete Orchestration Examples

#### Example A: System Settings
```text
User: "Open Wi-Fi settings"
  └─ Orchestrator receives prompt
  └─ NLRouter identifies action: open_settings (params: {target: "wifi"})
  └─ SystemControls dispatcher opens Windows ms-settings:network-wifi
  └─ ActionVerifier checks active window state
  └─ Result: "Opened Wi-Fi Settings."
```

#### Example B: Screen Observation
```text
User: "What can you see on my screen?"
  └─ Orchestrator verifies Screen Context is ON
  └─ ScreenObserver captures screenshot (excluding HELIOS UI overlay)
  └─ RapidOCR extracts on-screen text & active Win32 window metadata
  └─ Visual context payload injected into LLM reasoning
  └─ Result: "🖥️ Screen Observation [Google Chrome]: Currently observing Google Chrome..."
```

#### Example C: Commerce & Payment Preparation
```text
User: "Find a wireless keyboard under ₹2000 and prepare payment"
  └─ Guard 0.6 intercepts commercial intent
  └─ CommerceOrchestrator conducts multi-merchant web search (Tavily API)
  └─ Verifies direct product page URL & calculates transaction total
  └─ TransactionGuard checks amount limits & idempotency
  └─ UI renders interactive Payment Preview Card requiring explicit user click authorization
  └─ Result: "Payment prepared. Click [Authorize Payment] to proceed."
```

---

## Natural-Language Intent

HELIOS separates **what the user means** from **how the action is technically executed**. Users do not need to memorize exact command syntax.

- **General Intent Normalization**:
  - `"Open settings"`, `"Bring up system settings"`, and `"Take me to settings"` all map to generic settings resolution.
  - `"What can you see on my screen?"`, `"What is currently visible?"`, and `"Inspect my desktop"` all resolve to screen observation.
- **Target Specificity Preservation**:
  - Specific requests like `"Open Wi-Fi settings"` or `"Open Display settings"` preserve their exact target and open the corresponding sub-page rather than falling back to generic settings.

---

## CAHRA — Context Aware Hybrid Routing Algorithm

The **Context Aware Hybrid Routing Algorithm (CAHRA)** is the model-selection engine in HELIOS. It determines whether a request should be processed by a local LLM or escalated to a cloud model.

```text
    User Request
         │
         ▼
    Context Extraction (Prompt, Hardware, Internet, Keys)
         │
         ▼
    Feature Evaluation (Privacy, Freshness, Complexity)
         │
         ▼
    Constraint Engine (Force Local / Force Cloud)
         │
         ▼
    Model Utility Scoring (Local vs Cloud Profiles)
         │
         ▼
    Candidate Availability (Ollama, Gemini, OpenAI, OpenRouter, Groq)
         │
         ▼
    Explainability Engine (Decision Trace Logging)
         │
         ▼
    HybridLLM Execution
```

### Routing Dimensions

1. **Privacy Score ($R_p$)**: Detects sensitive keywords, personal credentials, or local data references. High privacy requirements force processing to local Ollama models.
2. **Freshness Score ($R_f$)**: Identifies queries requiring real-time internet information (e.g. current news, weather, live scores, web searches). High freshness queries trigger cloud model routing.
3. **Complexity Score ($R_c$)**: Evaluates query length, reasoning steps, and technical depth to allocate model capacity.
4. **Latency Score**: Estimates model response time based on local hardware capabilities versus cloud API ping.
5. **Cost Score**: Balances local zero-cost processing against cloud token budgets.

---

## How CAHRA Chooses a Model

1. **Feature Extraction**: Extracts quantitative scores for Privacy ($R_p$), Freshness ($R_f$), and Complexity ($R_c$) from the input text.
2. **Constraint Check**:
   - If internet is unavailable or local data is sensitive $\rightarrow$ **FORCE LOCAL**.
   - If prompt explicitly requests live web search or shopping $\rightarrow$ **FORCE CLOUD**.
3. **Utility Scoring**: Computes model utility for available local and cloud profiles using weighted candidate match scoring.
4. **Selection & Fallback**: Selects the candidate with highest utility. If the primary model fails or times out, CAHRA falls back to alternative available models.

---

## Local and Cloud Models

- **Local Processing**:
  - Uses [Ollama](https://ollama.com/) running models such as `gemma3`, `mistral`, or `llama3`.
  - Ensures full data privacy and offline capability.
- **Cloud Processing**:
  - **Google Gemini**: `gemini-3.6-flash` for high-speed live web queries.
  - **OpenAI**: `gpt-4o-mini` for complex reasoning.
  - **OpenRouter & Groq**: Dynamic free/open-tier cloud models.
- **Fallback Guarantee**: If local Ollama is offline when a cloud fallback is needed (or vice versa), HELIOS dynamically attempts alternative active model providers.

---

## Screen Context & Live Desktop Interaction

Visual interaction in HELIOS is **demand-driven** and strictly controlled by the **Screen Context** toggle.

```text
    Screen Context: OFF  ──►  Visual interactions blocked (Returns instruction notice)
    Screen Context: ON   ──►  Screen state acquired ONLY when request requires visual data
```

> [!IMPORTANT]
> **Screen Context ON does not mean HELIOS continuously records your screen.** Screenshot capture and window enumeration occur **only at the exact moment** a visual request (such as `"What can you see on my screen?"`) is issued.

### Screen Permission & Safety
- **Overlay Exclusion**: The `ScreenObserver` enumerates Win32 Z-order windows and excludes HELIOS's own UI overlay from captures so the agent does not inspect itself.
- **Foreground Safety Invariant**: HELIOS prevents sending keystrokes or mouse clicks to background windows while its own UI is focused, avoiding unintended user interactions.
- **Screen Permission Manager**: Prompts for explicit user confirmation when transmitting visual screen data to cloud models.

---

## Desktop Automation

HELIOS provides native Windows OS application and window control:

- **System Application Dispatcher**: Launches Windows Settings panels (`ms-settings:`), Chrome, Notepad, Calculator, Explorer, Bluetooth, and Wi-Fi.
- **Tab & Window Control**: Performs active tab closure (`Ctrl+W`) and window minimization (`Win+Down`).
- **Focus Transfer**: `ApplicationFocusManager` cleanly transfers Win32 window focus from the HELIOS dock to target user applications before executing actions.

---

## Verification Before Response

HELIOS applies state verification after executing desktop commands to confirm that actions succeeded before reporting results to the user.

```text
  Observe Current State (Pre-Execution Screen/Window Metadata)
               │
               ▼
         Execute Action
               │
               ▼
  Observe Resulting State (Post-Execution Window Check)
               │
               ▼
     StateVerifier Check (Window Title & Process Match)
         ┌─────┴─────┐
         ▼           ▼
      Verified    Unverified
         │           │
         │           ▼
         │     RecoveryEngine (1 Bounded Retry Attempt)
         │           │
         └─────┬─────┘
               ▼
        Final Response
```

### State Verification Architecture
- **`StateVerifier`**: Captures pre- and post-execution window titles, process names, and Z-order states. It verifies whether the target window became active.
- **`RecoveryEngine`**: If the initial window activation fails, the recovery engine performs one bounded retry attempt to re-focus the application.
- **Factual Scope**: The verifier checks OS window state and metadata. It does not perform full pixel-level image diffing or accessibility-tree DOM parsing.

---

## Documents, Files and RAG

HELIOS processes local user files:

- **File Parsing**: Extracts text from `.pdf`, `.docx`, `.txt`, `.md`, `.json`, `.csv`, and `.py`.
- **PDF Generation**: Converts document files (`.docx`, `.txt`, `.md`) to `.pdf` using ReportLab.
- **Local RAG**: `LocalRAGConnector` indexes local note files and retrieves relevant knowledge snippets for grounded answer generation.

---

## Web Search

- **Primary Provider**: Tavily API for structured live web search and product extraction.
- **Fallback Provider**: DuckDuckGo Search (`ddgs`) fallback when Tavily is unconfigured.
- **Browser Launch**: Opens verified product pages and search queries directly in the user's default web browser.

---

## Voice Input

- **Asynchronous STT**: SpeechRecognition listener integrated into the UI input dock.
- **Voice-to-Command Routing**: Transcribes spoken audio into text and passes it directly to the Orchestrator for intent processing.

---

## Notes and Reminders

- **Notes Management**: `NotesManager` provides CRUD operations for local notes saved in `data/notes/`.
- **Task Scheduler**: `TaskScheduler` (APScheduler) handles one-time reminders and background cron jobs.

---

## System Controls

- **Windows Settings Deep-Linking**: Maps natural language requests directly to Windows OS URI schemes (`ms-settings:display`, `ms-settings:network-wifi`, `ms-settings:bluetooth`, etc.).
- **System Volume & Brightness**: Controls hardware audio volume and display brightness.

---

## Commerce

HELIOS features an end-to-end 14-stage commercial research pipeline:

$$\text{DISCOVERING} \rightarrow \text{UNDERSTANDING} \rightarrow \text{RESEARCHING} \rightarrow \text{COMPARING} \rightarrow \text{RECOMMENDING} \rightarrow \text{CALCULATING} \rightarrow \text{TRANSACTION\_PREPARED} \rightarrow \text{REQUIRES\_AUTHORIZATION} \rightarrow \text{AUTHORIZED} \rightarrow \text{CHECKOUT} \rightarrow \text{PAYMENT} \rightarrow \text{VERIFYING} \rightarrow \text{VERIFIED}$$

- **Multi-Merchant Comparison**: Searches across Amazon, Flipkart, Croma, and other platforms to aggregate prices.
- **Direct Product Page Requirement**: Payment intent preparation requires a verified direct product page URL. Generic search pages or category listings are marked as informational research only.

---

## Payment and Payment Security

Security boundaries for financial operations are enforced outside LLM control:

```text
LLM Commerce Request ──► Price Verification ──► TransactionGuard Check
                                                       │
                                                       ▼
  User Click Authorization ◄── Payment Preview Card Rendered
         │
         ▼
  HMAC-SHA256 Signature Check ──► Razorpay Sandbox Order Creation ──► Verified Receipt
```

- **Explicit User Click Authorization**: The LLM **cannot** directly trigger a payment transaction. The user must physically click the **Authorize Payment** button on the UI preview card.
- **TransactionGuard Controls**:
  - **Amount Threshold Cap**: Limits single transactions to a configured maximum (default: ₹10,000 INR).
  - **Idempotency Protection**: Prevents duplicate payment submissions.
  - **HMAC-SHA256 Signature Verification**: Validates transaction payload integrity.
  - **Razorpay Sandbox Mode**: Executes orders in provider sandbox/test mode to prevent unintended charges.

---

## Privacy

- **Local-First Processing**: Sensitive prompts and local file indexing remain on the local machine.
- **Demand-Driven Capture**: Screenshot data is captured only when visually required and authorized.
- **Secret Masking**: API keys, payment tokens, and authorization headers are masked in log files and diagnostic UI displays.

---

## Architecture

```text
HELIOS_FINAL/
├── core/                       # Core decision, routing, commerce, and security engines
│   ├── commerce/               # Multi-merchant search, price comparison & product models
│   ├── desktop_session/        # Win32 screen observer, Z-order window resolver & session state
│   ├── payments/               # Razorpay bridge, TransactionGuard & payment authorization
│   ├── routing/                # CAHRA hybrid router, score engine & constraint engine
│   ├── action_verifier.py      # Desktop action execution verifier
│   ├── code_sandbox.py         # Isolated Python execution sandbox
│   ├── context_resolver.py     # Conversation memory & context dependency engine
│   ├── llm_engine.py           # Hybrid LLM engine (Ollama, Gemini, OpenAI, Groq, OpenRouter)
│   ├── local_rag.py            # Local document RAG connector
│   ├── nl_router.py            # Fast pre-LLM regex router & intent shortcuts
│   └── ocr_provider.py         # Local RapidOCR / Tesseract abstraction
├── modules/                    # Practical capability modules
│   ├── browser_agent.py        # Web search & Playwright browser tasks
│   ├── desktop_agent.py        # OS application control & file system operations
│   ├── document_processor.py   # Document text extraction & PDF generation
│   ├── notes_manager.py        # Local notes CRUD operations
│   ├── spreadsheet_agent.py    # Excel & CSV analytics engine
│   ├── system_controls.py      # Windows Settings & system control dispatcher
│   └── voice_input.py          # Asynchronous speech-to-text STT listener
├── ui/                         # Custom Tkinter glass UI suite
│   ├── chat_view.py            # Elevated glass response cards & streaming renderer
│   ├── header.py               # Glass header, 5-sphere avatar & model selector
│   ├── input_panel.py          # Command dock with file attachment & Screen Context toggle
│   ├── models_panel.py         # Model selection & management panel
│   └── theme.py                # Design tokens & color system
├── config/                     # Application routing rules & configuration files
├── data/                       # Sample demonstration datasets & local storage
├── docs/                       # Architecture documentation & technical reports
│   └── images/                 # Real-time execution screenshots
├── agent.py                    # HELIOSAgent Orchestrator controller
├── main.py                     # Main application entry point
├── helios_popup.py             # Full desktop UI application setup
├── requirements.txt            # Python dependency manifest
├── .env.example                # Environment configuration template
├── .gitignore                  # Git repository ignore rules
└── README.md                   # System documentation
```

---

## Project Structure

- `core/`: Main decision-making, routing, commerce, payment, and security logic.
- `modules/`: Practical capability modules for desktop control, OCR, documents, spreadsheets, and voice.
- `ui/`: Custom Tkinter desktop user interface with glassmorphism styling.
- `config/`: Application configuration and routing rule matrices.
- `data/`: Sample datasets and local storage folders.
- `docs/`: Technical documentation and screenshot assets.

---

## Installation

### Prerequisites
- **Operating System**: Windows 10 / 11 (64-bit)
- **Python**: Python 3.10 or higher
- **Local LLM (Optional)**: [Ollama](https://ollama.com/) with `gemma3` model (`ollama pull gemma3`)

### Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Bharath-723/HELIOS-Agent.git
   cd HELIOS-Agent
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**:
   ```bash
   copy .env.example .env
   ```
   Edit `.env` to supply your API keys (Gemini, OpenRouter, Tavily, etc.) if cloud capabilities are desired.

5. **Launch HELIOS**:
   ```bash
   python main.py
   ```

---

## Configuration

Key environment variables in `.env`:

| Variable | Required / Optional | Description | Default |
|---|---|---|---|
| `OLLAMA_BASE_URL` | Optional | URL for local Ollama server | `http://localhost:11434` |
| `OLLAMA_MODEL` | Optional | Default local Ollama model | `gemma3` |
| `LLM_MODE` | Required | Model routing mode (`auto`, `offline`, `online`) | `auto` |
| `CLOUD_PROVIDER` | Optional | Cloud provider choice (`gemini`, `gpt`, `groq`, `openrouter`) | `gemini` |
| `GEMINI_API_KEY` | Optional | Google Gemini API key | `your_gemini_api_key_here` |
| `GEMINI_MODEL` | Optional | Gemini model identifier | `gemini-3.6-flash` |
| `OPENROUTER_ENABLED`| Optional | Enable OpenRouter cloud LLM | `true` |
| `TAVILY_API_KEY` | Optional | Tavily web search API key | `your_tavily_api_key_here` |
| `RAZORPAY_MODE` | Optional | Payment sandbox mode | `sandbox` |
| `MAX_PAYMENT_AMOUNT_INR` | Optional | Max transaction safety threshold | `10000` |

---

## Usage Examples

### Example 1: General Question
```text
User: "What is 25 * 48?"
HELIOS: "1200"
```

### Example 2: Desktop Settings
```text
User: "Open Wi-Fi settings"
HELIOS: "Opened Wi-Fi Settings."
```

### Example 3: Screen Observation (Screen Context: ON)
```text
User: "What can you see on my desktop?"
HELIOS: "🖥️ Screen Observation [Google Chrome]: Currently observing Google Chrome..."
```

### Example 4: Document Reading & PDF Conversion
```text
User: "Convert report.docx into a PDF file"
HELIOS: "Successfully converted 'report.docx' to PDF -> report.pdf"
```

### Example 5: Commerce Research & Price Comparison
```text
User: "Search for a todo book on all shopping platforms"
HELIOS: "🛍️ Research & Recommendation for Todo Book:
Recommended: Daily Task Planner & Todo Journal
Price: ₹299.00 (Search-result price) | Merchant: Amazon.in
Merchant Offer Comparison:
  • Amazon.in: ₹299.00
  • Flipkart.com: ₹349.00"
```

---

## Limitations

- **Windows OS Dependency**: Desktop window enumeration and UI automation rely on Windows Win32 APIs.
- **Local Model Hardware**: Performance of local Ollama models depends on available CPU/GPU and RAM resources.
- **OCR Resolution Scope**: RapidOCR text extraction accuracy depends on screen resolution, text size, and font rendering.
- **Dynamic Web Sites**: Web search parsing depends on search provider API structure.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
