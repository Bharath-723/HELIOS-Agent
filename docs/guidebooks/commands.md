# 📋 HELIOS Natural-Language Command Reference Guide

This reference guide lists all natural-language command patterns, action parameters, and executable capabilities supported by the **HELIOS** agent.

---

## 1. 📄 File & Document Operations

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Convert to PDF** | `"convert essay.txt to pdf"`<br>`"make a pdf of resume.docx"` | `convert_to_pdf` | Converts `.txt`, `.docx`, or `.md` files to PDF using ReportLab. |
| **Create File** | `"create file note.txt on desktop with content Hello"` | `create_file` | Creates a new text file on Desktop or Documents directory. |
| **Find / Search File** | `"search for tax report on my local pc"`<br>`"find presentation.pptx"` | `find_file` | Recursively searches for files matching a keyword in user directories. |
| **List Folder** | `"list files in downloads"`<br>`"show files on desktop"` | `list_folder` | Lists directory contents for Downloads, Desktop, Documents, etc. |
| **Search In File** | `"find python in notes.txt"` | `search_in_file` | Scans text lines inside a specific file to locate keyword matches. |
| **Move File** | `"move report.pdf from desktop to documents"` | `move_file` | Relocates a file between user subdirectories. |
| **Delete File** | `"delete draft.txt"` | `delete_file` | Permanently deletes a file from disk (*Requires confirmation*). |

---

## 2. 🖥️ Windows System Controls & Application Control

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **System Settings** | `"open wifi settings"`<br>`"open bluetooth settings"`<br>`"open display settings"` | `open_settings` | Directly opens Windows OS settings sub-pages via `ms-settings:` URI schemes. |
| **Launch App** | `"open chrome"`<br>`"launch notepad"`<br>`"open calculator"` | `launch_app` | Launches Windows applications (Chrome, Notepad, Calculator, VS Code, Explorer). |
| **Close Tab** | `"close youtube tab"`<br>`"close browser tab"` | `close_tab` | Sends `Ctrl+W` shortcut to close active browser tab. |
| **Minimize Window** | `"minimize window"`<br>`"click minimize button"` | `minimize_window` | Sends `Win+Down` shortcut to minimize active window. |
| **Volume Control** | `"set volume to 50"`, `"volume up"`, `"mute"` | `volume_set`, `mute` | Controls system master audio volume. |
| **Brightness** | `"set brightness to 70"`, `"dim screen"` | `brightness_set` | Adjusts laptop screen display brightness. |
| **Dark Mode** | `"turn on dark mode"`, `"turn off dark mode"` | `dark_mode_on` | Toggles Windows OS personalization theme settings. |
| **Night Light** | `"turn on night light"`, `"is night light on"` | `night_light_on` | Controls display color temperature. |
| **Power Saver** | `"turn on energy saver"`, `"battery saver mode"` | `power_saver` | Overrides Windows active power scheme. |
| **Hardware Radios** | `"turn on wifi"`, `"turn on bluetooth"`, `"hotspot on"` | `wifi_on`, `bluetooth_on` | Manages Wi-Fi, Bluetooth, and Mobile Hotspot hardware radios. |

---

## 3. 👁️ Visual Screen Observation

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Screen Inspection** | `"what can you see on my screen?"`<br>`"describe my desktop"` | `screen_observation` | Captures desktop screenshot on demand, excludes HELIOS UI overlay, extracts text via RapidOCR, and grounds reasoning. (*Requires Screen Context: ON*) |
| **Session Control** | `"stop desktop session"`, `"cancel session"` | `stop_session` | Terminates active visual desktop automation session. |

---

## 4. 🌐 Web Browsing & Online Search

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Web Search** | `"search for latest AI news on Google"`<br>`"weather in Tokyo"` | `search_google` | Conducts real-time web search using Tavily API or DuckDuckGo fallback. |
| **Open Website** | `"open github.com"`, `"open youtube.com"` | `open_website` | Opens target web URL directly in default web browser. |
| **YouTube Search** | `"play lofi on youtube"`, `"search youtube for tutorials"` | `search_youtube` | Searches YouTube online and opens video result. |

---

## 5. 🛍️ Commerce Research & Price Comparison

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Multi-Merchant Search** | `"search for a todo book on all shopping platforms"`<br>`"find wireless keyboard under ₹2000"` | `commerce_research` | Conducts multi-merchant search across Amazon, Flipkart, Croma, compares prices, and verifies direct product pages. |
| **Payment Preparation** | `"prepare payment for Logitech keyboard"`, `"buy Logitech K120"` | `prepare_payment` | Validates product page, checks `TransactionGuard` limits, and renders Payment Preview Card requiring explicit user click authorization. |

---

## 6. 📝 Notes & Knowledge Base (Local RAG)

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Create Note** | `"create note titled Meeting with content Discuss architecture"` | `create_note` | Saves a new text note into `data/notes/`. |
| **Read Notes** | `"read note titled Meeting"`, `"show my notes"` | `read_note` | Retrieves note content from local storage. |
| **Local RAG Search** | `"find safety SOP in local notes"` | `retrieve_sop` | Searches local note index and retrieves grounded knowledge snippets. |

---

## 7. ⏰ Reminders & Task Scheduling

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Schedule Reminder** | `"remind me in 10 minutes to join meeting"` | `schedule_task` | Adds an APScheduler background timer job with chat popup notification. |
| **List Reminders** | `"show my tasks"`, `"list reminders"` | `list_tasks` | Displays active scheduled background reminder tasks. |
| **Cancel Reminder** | `"cancel task 4c8b327e"` | `cancel_task` | Cancels a scheduled task by ID. |

---

## 8. 📊 Spreadsheet Processing & Data Analytics

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Analyze Spreadsheet** | `"analyze sales.xlsx"`<br>`"calculate total revenue in data.csv"` | `analyze_spreadsheet` | Parses `.xlsx` or `.csv` files, filters rows, aggregates column metrics, and generates summary reports. |

---

## 9. 💻 Sandboxed Code Execution

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Run Python Code** | `"run this python calculation safely"`<br>`"execute script to compute prime numbers"` | `run_sandbox_code` | Runs generated Python code in an isolated subprocess with 5-second execution timeouts and secret masking. |

---

## 10. 📧 Email & Communication

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Gmail Compose** | `"compose email to john@example.com with subject Meeting"` | `compose_gmail` | Opens draft window with pre-filled recipient, subject, and generated body. |
| **Open Gmail** | `"open my gmail inbox"` | `open_gmail` | Opens `mail.google.com` in browser. |

---

## 11. 🔧 Diagnostics & System Utilities

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **System Info** | `"system info"`, `"show cpu and ram usage"` | `system_info` | Reports active CPU percentage, available RAM, and OS metadata. |
| **Battery Status** | `"battery status"`, `"check battery percentage"` | `battery` | Checks charging state and battery percentage. |
| **IP Address** | `"what is my ip address"` | `ip_address` | Reports local IP and network interface addresses. |
| **Running Apps** | `"what apps are running"` | `running_apps` | Lists active non-system process names. |
| **Kill Process** | `"close Chrome"`, `"kill notepad"` | `kill_app` | Force-closes process by name (*Requires confirmation*). |
| **Maintenance** | `"flush dns"`, `"empty recycle bin"` | `flush_dns`, `empty_recycle` | Flushes DNS cache or empties Recycle Bin. |

---

## 12. 🤖 Offline LLM & Model Control

| Feature | Prompt Pattern Examples | Action Mapping | Description |
| :--- | :--- | :--- | :--- |
| **List Models** | `"list ollama models"` | `ollama_list` | Reports locally installed Ollama models. |
| **Pull Model** | `"pull gemma3 model"` | `ollama_pull` | Pulls model layers from Ollama registry. |
| **Model Selection** | `"MODEL: AUTO"`, `"MODEL: LOCAL"`, `"MODEL: CLOUD"` | `set_model_mode` | Switches routing mode between AUTO, LOCAL (gemma3), or CLOUD. |
