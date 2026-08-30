# HELIOS

HELIOS is an autonomous desktop AI agent that connects natural-language user requests to local or cloud AI models and practical operating tools. It unifies document processing, desktop automation, visual screen observation, web search, spreadsheet analytics, sandboxed code execution, and safe commerce research while applying strict explicit authorization boundaries where actions have side effects.

---

## Table of Contents
1. [What HELIOS Does](#1-what-helios-does)
2. [How HELIOS Works](#2-how-helios-works)
3. [The Orchestrator](#3-the-orchestrator)
4. [AI Model Routing (CAHRA)](#4-ai-model-routing-cahra)
5. [Visual Screen Observation](#5-visual-screen-observation)
6. [Desktop Automation](#6-desktop-automation)
7. [Browser Automation](#7-browser-automation)
8. [Documents, OCR and Local RAG](#8-documents-ocr-and-local-rag)
9. [Spreadsheet Processing](#9-spreadsheet-processing)
10. [Sandboxed Code Execution](#10-sandboxed-code-execution)
11. [Commerce Research & Product Comparison](#11-commerce-research--product-comparison)
12. [Payment Safety & TransactionGuard](#12-payment-safety--transactionguard)
13. [Privacy Architecture](#13-privacy-architecture)
14. [Failure Handling & Resilience](#14-failure-handling--resilience)
15. [Project Structure](#15-project-structure)
16. [Installation](#16-installation)
17. [Configuration](#17-configuration)
18. [Usage Examples](#18-usage-examples)
19. [Security Model](#19-security-model)
20. [Limitations](#20-limitations)
21. [License](#21-license)

---

## 1. What HELIOS Does

HELIOS simplifies desktop interactions by allowing users to communicate using natural language instead of memorizing specific software menus, CLI flags, or hotkeys.

### Implemented Capabilities

| Capability | Scope & Processing | Key Operations | Read / Action |
|---|---|---|:---:|
| **Natural Language Interaction** | Local / Cloud | Converts freeform English requests into structured actions or conversational answers | Read |
| **CAHRA Model Routing** | System Engine | Dynamically selects between local Ollama models (`gemma3`, `mistral`) and cloud LLMs (`gemini-3.6-flash`, `gpt-4o-mini`, `openrouter`) based on privacy, freshness, and hardware constraints | Read |
| **Screen Observation** | Demand-Driven Local | Captures desktop screenshot on demand, enumerates Win32 Z-order windows, extracts text via RapidOCR, and grounds reasoning | Read |
| **Desktop Automation** | Native Local API | Opens applications (`Chrome`, `Settings`, `Notepad`, `Calculator`), closes browser tabs (`Ctrl+W`), minimizes windows (`Win+Down`), and controls volume/brightness | Action |
| **Browser Automation** | Web / Local | Opens web URLs, conducts web searches via Tavily & DuckDuckGo API, and reads web content | Action |
| **Document Processing & Conversion** | Local File System | Extracts text from PDF, DOCX, TXT, MD, and converts documents to PDF using ReportLab | Read / Action |
| **Local RAG Retrieval** | Local Storage | Searches local notes and index entries to answer questions grounded in local knowledge | Read |
| **Spreadsheet Processing** | Local File System | Ingests `.xlsx` and `.csv` files, filters rows, aggregates columns, and calculates metrics | Read |
| **Sandboxed Code Execution** | Isolated Process | Runs generated Python code in a sandboxed subprocess with strict execution timeouts | Action |
| **Commerce Research** | Web API | Searches multiple online platforms (Amazon, Flipkart, etc.), compares prices, and verifies direct product pages | Read |
| **Payment Preparation & Verification** | Sandbox / API Boundary | Generates Razorpay payment previews with HMAC signatures and requires explicit user authorization before order creation | Action |

---

## 2. How HELIOS Works

HELIOS follows a strict, end-to-end execution pipeline from user input to verified result:

```text
  User Request (Text / Voice STT / CLI)
                  │
                  ▼
   Natural Language Router & Fast Shortcuts (NLRouter)
                  │
                  ▼
       Agent Orchestrator (HELIOSAgent)
                  │
     ┌────────────┴────────────┐
     ▼                         ▼
Pre-Routing Guards      Context Resolver
(Commerce / Session)    (Conversation Memory)
     │                         │
     └────────────┬────────────┘
                  ▼
       CAHRA Model Router
  (Hardware / Privacy / Freshness)
                  │
     ┌────────────┼────────────┐
     ▼            ▼            ▼
Local Ollama   Cloud Gemini  Cloud GPT / OpenRouter
(`gemma3`)     (`flash-3.6`) (`gpt-4o-mini`)
     │            │            │
     └────────────┼────────────┘
                  ▼
        Capability Execution
  (Desktop / Docs / Web / Sandbox / Commerce)
                  │
                  ▼
         Action Verifier
  (Win32 State / Target Match Verification)
                  │
                  ▼
        Response Generator
  (Prefix Sanitization & Markdown UI Display)
```

---

## 3. The Orchestrator

The **Orchestrator** (implemented in [`agent.py`](file:///d:/HELIOS_FINAL/HELIOS_FINAL/agent.py) as `HELIOSAgent`) is the central coordinator of HELIOS.

### Responsibilities of the Orchestrator
1. **Receives User Requests**: Accepts text input from the floating glass dock, voice STT, or terminal CLI.
2. **Evaluates Pre-Routing Safety Guards**:
   - **Guard 0.58 (Desktop Session)**: Intercepts active desktop automation instructions and checks screen privacy policies.
   - **Guard 0.6 (Commerce & Payments)**: Intercepts shopping, pricing, and payment requests, delegating them to `CommerceOrchestrator` before general chat routing.
3. **Resolves Semantic Intent**: Uses fast pre-LLM regex shortcuts in `NLRouter` to map queries like `"What do you see?"` to `SCREEN_OBSERVATION` or `"Bring up settings"` to `open_settings`.
4. **Dispatches to Capability Modules**: Invokes the appropriate engine (`DesktopSessionManager`, `DocumentProcessor`, `OCRProvider`, `LocalRAGConnector`, `CodeSandbox`, `CommerceOrchestrator`, `SpreadsheetAgent`).
5. **Verifies Execution Results**: Evaluates action outcomes via `ActionVerifier` to ensure target application windows opened correctly.
6. **Formats & Sanitizes Output**: Removes duplicate assistant prefixes and delivers grounded markdown cards to the UI.

---

## 4. AI Model Routing (CAHRA)

HELIOS uses the **Capability-Aware Hybrid Routing Algorithm (CAHRA)** to select the optimal LLM for every task.

### How CAHRA Works
- **Local-First Architecture**: When offline or processing local files, HELIOS routes to local Ollama models (`gemma3`, `mistral`).
- **Dynamic Cloud Escalation**: When `LLM_MODE=auto` and internet is available, CAHRA evaluates:
  - **Freshness Score**: High freshness prompts (e.g. web search, current prices, live news) route to Cloud (`gemini-3.6-flash` or `gpt-4o-mini`).
  - **Privacy Score**: Prompts containing sensitive credentials or local notes route to Local models to protect privacy.
  - **Hardware Resources**: Monitors available RAM and CPU load to adjust local inference expectations.
- **Fallback Behavior**: If a cloud API request fails or times out, HELIOS seamlessly falls back to local inference.

---

## 5. Visual Screen Observation

Visual observation in HELIOS is **demand-driven** and privacy-aware.

### Key Principles
- **No Constant Streaming**: HELIOS does **not** record or stream your desktop continuously. Screen capture occurs only when a visual request (such as `"What can you see on my screen?"`) is issued and `SCREEN CONTEXT` is enabled.
- **Overlay Exclusion**: The `ScreenObserver` uses Win32 Z-order window enumeration to detect the top-most user application while excluding HELIOS's own floating UI overlay from screenshot captures.
- **RapidOCR Integration**: Extracted screenshots are analyzed by `OCRProvider` (RapidOCR) to parse visible window titles and on-screen text into a visual context payload for the reasoning model.

---

## 6. Desktop Automation

HELIOS interacts directly with Windows desktop applications using native Win32 APIs and PyAutoGUI.

### Capability Scope
- **Application Control**: Opens system Settings, Chrome, Notepad, Calculator, Explorer, Bluetooth, and Wi-Fi panels.
- **Tab & Window Control**: Closes browser tabs (`Ctrl+W`) and minimizes active windows (`Win+Down`).
- **Target Resolution**: Uses `ScreenTargetResolver` and `ActionVerifier` to confirm that the requested window is in the foreground before taking action.

---

## 7. Browser Automation

HELIOS performs bounded web and browser tasks:

- **Web Search**: Queries Tavily API or DuckDuckGo fallback for real-time web results.
- **URL Launching**: Opens verified product pages and search queries in the user's default browser.
- **Controlled Boundaries**: HELIOS does not store browser credentials or execute unauthorized form submissions.

---

## 8. Documents, OCR and Local RAG

HELIOS handles multi-format local document understanding:

- **Supported Formats**: Reads `.pdf`, `.docx`, `.txt`, `.md`, `.json`, `.csv`, `.py`.
- **PDF Generation**: Converts document files (`.docx`, `.txt`, `.md`) to `.pdf` using ReportLab.
- **Local RAG**: Searches local note indexes and documents via `LocalRAGConnector` to answer queries grounded in local data.

---

## 9. Spreadsheet Processing

The `SpreadsheetAgent` processes tabular dataset files (`.xlsx`, `.csv`):

- **Data Ingestion**: Parses sheets into structured table views.
- **Column Analytics**: Calculates totals, averages, min/max metrics, and filters rows based on user criteria.
- **Report Generation**: Produces clean summary breakdowns for user display.

---

## 10. Sandboxed Code Execution

HELIOS provides isolated Python script execution via `CodeSandbox`:

- **Subprocess Isolation**: Generated Python code is executed in an isolated process with strict 5-second timeouts.
- **Output Capture**: Captures stdout and stderr without exposing internal environment variables or system secrets.
- **Failure Safety**: If script execution fails or times out, HELIOS returns a structured execution error notice.

---

## 11. Commerce Research & Product Comparison

HELIOS features an end-to-end commercial research pipeline:

- **Multi-Merchant Search**: Searches products across major online platforms (Amazon, Flipkart, Croma, etc.) via Tavily API.
- **Price Comparison**: Aggregates merchant offers, verifies direct product page URLs, and highlights the lowest verified price.
- **Direct Page Verification**: Distinguishes between direct product page links and generic search result URLs.

---

## 12. Payment Safety & TransactionGuard

HELIOS enforces strict, non-negotiable security boundaries for commerce and payment workflows:

```text
User Shopping Request ──► Commerce Research ──► Price Verification
                                                      │
                                                      ▼
Authorization Button ◄── Payment Preview Card ◄── TransactionGuard Check
         │                                       (Amount Limit & Idempotency)
         ▼
User Click Authorization ──► HMAC Signature Verification ──► Provider Sandbox Order
```

- **Explicit User Authorization**: HELIOS **never** executes a payment automatically. The user must explicitly click the **Authorize Payment** button in the UI card.
- **Amount Thresholds**: Enforces a strict maximum transaction limit (default: ₹10,000 INR).
- **HMAC Signature Verification**: Generates and verifies HMAC-SHA256 signatures for order verification.
- **Provider Sandbox Mode**: Operates in Razorpay sandbox/test mode to prevent unintended real-world financial charges.

---

## 13. Privacy Architecture

- **Local-First Design**: Sensitive data, local notes, and local files remain on your machine.
- **Demand-Driven Capture**: Screenshots are captured strictly when authorized and requested.
- **Credential Protection**: API keys and secrets in `.env` are masked in logs and UI activity diagnostics.

---

## 14. Failure Handling & Resilience

HELIOS prioritizes **controlled failures over fabricated results**:
- If web search yields no live results, HELIOS informs the user instead of inventing fake product prices.
- If a target window cannot be verified, `ActionVerifier` marks the action as unverified and reports the failure.
- If cloud APIs time out, HELIOS falls back gracefully to local Ollama inference.

---

## 15. Project Structure

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
├── agent.py                    # HELIOSAgent Orchestrator controller
├── main.py                     # Main application entry point
├── helios_popup.py             # Full desktop UI application setup
├── requirements.txt            # Python dependency manifest
├── .env.example                # Environment configuration template
├── .gitignore                  # Git repository ignore rules
└── README.md                   # System documentation
```

---

## 16. Installation

### Prerequisites
- **Operating System**: Windows 10 / 11 (64-bit)
- **Python**: Python 3.10 or higher
- **Local LLM (Optional)**: [Ollama](https://ollama.com/) with `gemma3` model (`ollama pull gemma3`)

### Step-by-Step Setup

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

## 17. Configuration

HELIOS is configured using environment variables in `.env`:

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

## 18. Usage Examples

### Example 1: Document Processing & PDF Conversion
```text
User: "Convert sample_report.docx into a PDF file"
HELIOS: "Successfully converted 'sample_report.docx' to PDF -> sample_report.pdf"
```

### Example 2: Visual Screen Observation
```text
User: "What can you see on my desktop?" (Screen Context: ON)
HELIOS: "🖥️ Screen Observation [Google Chrome]: Currently observing Google Chrome. Visible elements include tab bar, search input, and web article text..."
```

### Example 3: System Controls
```text
User: "Open Wi-Fi settings"
HELIOS: "Opened Wi-Fi Settings."
```

### Example 4: Commerce Research & Price Comparison
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

## 19. Security Model

HELIOS implements multiple safety layers:
- **Authorization Boundaries**: Side-effecting actions (payments, file deletions, system changes) require explicit user permission.
- **Sandbox Isolation**: Generated code runs in an isolated Python process with strict resource timeouts.
- **Verification Engine**: Actions are verified post-execution via `ActionVerifier` to ensure expected system states.
- **Secret Protection**: API keys and tokens are excluded from logging and UI card displays.

---

## 20. Limitations

- **Windows OS Dependency**: Desktop window enumeration and UI automation rely on Windows Win32 APIs.
- **Local Model Hardware**: Performance of local Ollama models depend on available CPU/GPU and RAM.
- **OCR Accuracy**: RapidOCR extraction accuracy is subject to screen resolution and font rendering.
- **Dynamic Web Sites**: Web page structure changes can affect web search parsing.

---

## 21. License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
