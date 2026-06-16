# 🌌 HELIOS — Autonomous Desktop Agent

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Local LLM](https://img.shields.io/badge/Ollama-gemma3%20%7C%20mistral-orange.svg?logo=ollama&logoColor=white)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Repository](https://img.shields.io/badge/GitHub-HELIOS--Agent-brightgreen.svg?logo=github&logoColor=white)](https://github.com/Bharath-723/HELIOS-Agent)

**HELIOS** (*Hybrid Extensible Language Intelligence Operating System*) is a premium, offline-first intelligent desktop automation and assistance system. It leverages natural language processing (local LLMs via Ollama) and advanced system APIs to automate workflows, manage files, control system hardware, write documents, and coordinate tools — all directly on your Windows PC through a clean chat interface.

---

## 🌟 Key Features

### 🤖 1. NLU Router & Context-Aware Action Dispatcher
* Fast, lightweight natural language routing using offline local models (`gemma3`, `mistral`) with cloud API fallback (`Gemini 2.0 Flash`, `GPT-4o-mini`).
* Direct programmatic shortcutting for attached files and follow-up prompts to maintain reliable action mapping.

### 🖥️ 2. Zero-Redirection System Controls
* **Direct Hardware Toggles**: Turn ON/OFF system configurations instantly without opening Windows Settings pages.
* **Night Light**: Silent command-line scheduling and control via `nightlight-cli` (under 100ms execution).
* **Mobile Hotspot**: Programmatic WinRT-powered radio management.
* **Energy Saver**: Seamless toggling between maximum power efficiency schemes (`SCHEME_MAX`) and balanced setups (`SCHEME_BALANCED`).
* **Airplane Mode & Bluetooth**: Low-level WinRT radio API toggling.
* **Wi-Fi controls**: Dynamic adapter fetching, status checks, and safe elevated execution using threaded Windows UAC dialog consent prompts.

### 📄 3. Intelligent PDF Conversion (TXT & DOCX)
* Programmatic generation of `.pdf` files from plain text (`.txt`, `.py`, `.json`, etc.) or rich `.docx` word documents using `reportlab`.
* Automatic font cleaning to prevent encoding crashes when dealing with Windows typography, quotes, dashes, or bullet characters.
* Direct integration with file explorer search: resolves partial names or asks for clarification (disambiguation) if multiple file matches are found.

### 📅 4. Tool Orchestration & Multi-Step Flows
* **Gmail Integration**: Drafts, composes, and sends emails instantly.
* **Web Search**: Dynamic routing for online lookups, YouTube video playbacks, and Swiggy/Zomato restaurant searches.
* **Task Scheduling**: Integrated scheduler to trigger reminders or system tasks using natural language timing (*"remind me in 15 mins to drink water"*).
* **Notes Management**: Local note-taking library for easy storage, listing, and lookup.

---

## ⌨️ Prompts Examples

| Category | Example Prompt | Action Performed |
| :--- | :--- | :--- |
| **PDF Conversion** | `"convert IKS_Consolidated_Study_Guide.docx to pdf"` | Searches local PC, compiles to PDF, opens it |
| **System Toggle** | `"turn on night light"` | Programmatic display temperature adjustment |
| **Power Saver** | `"turn on energy saver"` | Switches OS active power scheme to Power Saver |
| **Hotspot** | `"hotspot status"` | Queries operational state of WinRT Hotspot radio |
| **Media Playback** | `"play lofi on youtube"` | Searches and plays directly in browser |
| **File Search** | `"find thesis in my local pc"` | Performs local file search with details |
| **Scheduling** | `"remind me in 10 minutes to take break"` | Sets a background timer and triggers notification |

---

## 🛠️ Installation & Setup

### Requirements
* Windows 10/11
* Python 3.10+
* [Ollama](https://ollama.com/) (installed and running)

### Step-by-Step Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Bharath-723/HELIOS-Agent.git
   cd HELIOS-Agent
   ```

2. **Create & Activate Virtual Environment:**
   ```bash
   python -m venv venv
   # Activate on Windows:
   .\venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node Dependency (for Night Light CLI):**
   Ensure Node.js is installed, then cache the tool:
   ```bash
   npx nightlight-cli --help
   ```

5. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   # Local LLM
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=gemma3

   # Cloud Fallbacks (Optional)
   CLOUD_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash

   # Mode (offline, online, auto)
   LLM_MODE=auto

   TIMEZONE=Asia/Kolkata
   ```

6. **Download Local LLM Model:**
   ```bash
   ollama pull gemma3
   ```

7. **Run the Application:**
   * Run the CLI application:
     ```bash
     python main.py
     ```
   * Or run the graphical popup application:
     ```bash
     python helios_popup.py
     ```

---

## 📁 Project Structure

```text
HELIOS-Agent/
├── core/
│   ├── llm_engine.py      # Local (Ollama) & Cloud (Gemini/GPT) LLM handlers
│   └── nl_router.py       # Natural language command router & rules system
├── modules/
│   ├── chat_history.py    # Session storage for prompts and results
│   ├── desktop_agent.py   # Shell, Volume, and OS utility actions
│   ├── file_creator.py    # Local file creator and PDF engine
│   └── system_controls.py # Wi-Fi, Bluetooth, Hotspot, and Power toggles
├── data/                  # Local notes and chat histories storage
├── requirements.txt       # Project python dependencies
├── main.py                # Command-line interface entry point
├── helios_popup.py        # Graphical user interface (GUI) popup launcher
└── agent.py               # Central HELIOS orchestrator and state-machine
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

* **M Bharath** — *Creator & Lead Developer* — [Bharath-723](https://github.com/Bharath-723)
