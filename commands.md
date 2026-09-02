# 📋 HELIOS Natural-Language Command Reference Guide

Welcome to the **HELIOS Command Reference Guide**. HELIOS interprets freeform English prompts and maps them directly to functional desktop, web, system, document, and AI capabilities.

This guide provides an exhaustive list of supported natural-language prompt patterns, action mappings, and operational descriptions.

---

## 1. 📄 File & Document Operations

Commands for searching, creating, converting, moving, and managing local files and documents.

### 1.1 Convert File to PDF
* **Action Mapping**: `convert_to_pdf`
* **Description**: Locates `.txt`, `.docx`, or `.md` files on your system, compiles them into a clean PDF using ReportLab, and opens the output file.
* **Example Prompts**:
  * 💬 `"convert essay.txt to pdf"`
  * 💬 `"make a pdf of resume.docx"`
  * 💬 `"convert notes.md into a pdf document"`

---

### 1.2 Create File
* **Action Mapping**: `create_file`
* **Description**: Creates a new text file in the Desktop or Documents folder with optional pre-filled content.
* **Example Prompts**:
  * 💬 `"create file note.txt on desktop with content Hello"`
  * 💬 `"create a new text file draft.txt on my desktop"`

---

### 1.3 Find / Search File
* **Action Mapping**: `find_file`
* **Description**: Recursively scans user directories (Desktop, Documents, Downloads, etc.) to locate files matching a keyword.
* **Example Prompts**:
  * 💬 `"search for tax report on my local pc"`
  * 💬 `"find presentation.pptx on my computer"`
  * 💬 `"search for project proposal in documents"`

---

### 1.4 List Folder Contents
* **Action Mapping**: `list_folder`
* **Description**: Lists files and subdirectories located inside user folders.
* **Example Prompts**:
  * 💬 `"list files in downloads"`
  * 💬 `"show files on desktop"`
  * 💬 `"list files in documents folder"`

---

### 1.5 Search Keywords Inside File
* **Action Mapping**: `search_in_file`
* **Description**: Opens a specific text document and scans line-by-line to locate keyword occurrences.
* **Example Prompts**:
  * 💬 `"find python in notes.txt"`
  * 💬 `"search for error in log.txt"`

---

### 1.6 Move File
* **Action Mapping**: `move_file`
* **Description**: Relocates a specified file from one user directory to another.
* **Example Prompts**:
  * 💬 `"move report.pdf from desktop to documents"`
  * 💬 `"move photo.png from downloads to pictures"`

---

### 1.7 Delete File
* **Action Mapping**: `delete_file`
* **Description**: Permanently removes a file from disk (*Requires explicit user confirmation*).
* **Example Prompts**:
  * 💬 `"delete draft.txt"`
  * 💬 `"remove temp_notes.txt from desktop"`

---

## 2. 🖥️ Windows System Controls & App Control

Commands for launching Windows applications, managing settings sub-pages, tab/window controls, and hardware radios.

### 2.1 System Settings Sub-Pages
* **Action Mapping**: `open_settings`
* **Description**: Opens Windows OS settings sub-pages directly using native `ms-settings:` URI schemes.
* **Example Prompts**:
  * 💬 `"open wifi settings"`
  * 💬 `"open bluetooth settings"`
  * 💬 `"open display settings"`
  * 💬 `"open sound settings"`
  * 💬 `"open storage settings"`
  * 💬 `"open windows update"`

---

### 2.2 Application Launching
* **Action Mapping**: `launch_app`
* **Description**: Launches Windows desktop applications directly.
* **Example Prompts**:
  * 💬 `"open chrome"`
  * 💬 `"launch notepad"`
  * 💬 `"open calculator"`
  * 💬 `"open file explorer"`
  * 💬 `"open vscode"`

---

### 2.3 Browser Tab & Window Control
* **Action Mapping**: `close_tab` / `minimize_window`
* **Description**: Performs keyboard shortcuts to close the active browser tab (`Ctrl+W`) or minimize the active window (`Win+Down`).
* **Example Prompts**:
  * 💬 `"close youtube tab"`
  * 💬 `"close current browser tab"`
  * 💬 `"minimize window"`
  * 💬 `"click minimize button on my screen"`

---

### 2.4 Volume & Audio Controls
* **Action Mapping**: `volume_set` / `mute`
* **Description**: Adjusts master system audio volume or toggles mute.
* **Example Prompts**:
  * 💬 `"set volume to 50"`
  * 💬 `"volume up"`
  * 💬 `"volume down"`
  * 💬 `"mute volume"`
  * 💬 `"unmute"`

---

### 2.5 Screen Brightness
* **Action Mapping**: `brightness_set`
* **Description**: Programmatically adjusts laptop display brightness.
* **Example Prompts**:
  * 💬 `"set brightness to 70"`
  * 💬 `"increase brightness"`
  * 💬 `"dim screen"`

---

### 2.6 Dark Mode & Personalization
* **Action Mapping**: `dark_mode_on` / `dark_mode_off`
* **Description**: Toggles Windows OS dark and light personalization themes via Registry update.
* **Example Prompts**:
  * 💬 `"turn on dark mode"`
  * 💬 `"turn off dark mode"`

---

### 2.7 Night Light & Energy Saver
* **Action Mapping**: `night_light_on` / `power_saver`
* **Description**: Toggles display color temperature and overrides active Windows power schemes.
* **Example Prompts**:
  * 💬 `"turn on night light"`
  * 💬 `"is night light on"`
  * 💬 `"turn on energy saver"`
  * 💬 `"enable battery saver mode"`

---

### 2.8 Hardware Radios (Wi-Fi, Bluetooth, Hotspot, Airplane Mode)
* **Action Mapping**: `wifi_on` / `bluetooth_on` / `hotspot_on` / `airplane_mode_on`
* **Description**: Programmatically controls wireless hardware adapters using WinRT APIs.
* **Example Prompts**:
  * 💬 `"turn on wifi"`
  * 💬 `"turn off wifi"`
  * 💬 `"turn on bluetooth"`
  * 💬 `"turn off bluetooth"`
  * 💬 `"turn on mobile hotspot"`
  * 💬 `"turn on airplane mode"`

---

## 3. 👁️ Visual Screen Observation

Commands for observing on-screen content and active window states (*Requires Screen Context: ON*).

### 3.1 Inspect Desktop State
* **Action Mapping**: `screen_observation`
* **Description**: Captures desktop screenshot on demand, excludes HELIOS UI overlay, enumerates Win32 Z-order windows, extracts text via RapidOCR, and grounds reasoning.
* **Example Prompts**:
  * 💬 `"what can you see on my screen?"`
  * 💬 `"describe my desktop"`
  * 💬 `"what is currently visible?"`
  * 💬 `"look at my screen and tell me what is open"`

---

### 3.2 Terminate Desktop Session
* **Action Mapping**: `stop_session`
* **Description**: Terminates active visual desktop automation session.
* **Example Prompts**:
  * 💬 `"stop desktop session"`
  * 💬 `"cancel session"`

---

## 4. 🌐 Web Browsing & Online Search

Commands for searching online, reading web pages, and launching web sites.

### 4.1 Live Web Search
* **Action Mapping**: `search_google`
* **Description**: Conducts real-time web search via Tavily API or DuckDuckGo fallback and returns grounded information.
* **Example Prompts**:
  * 💬 `"search for latest AI news on Google"`
  * 💬 `"what is the current weather in Tokyo"`
  * 💬 `"look up python 3.12 release notes online"`

---

### 4.2 Open Website
* **Action Mapping**: `open_website`
* **Description**: Opens specified website URL directly in default web browser.
* **Example Prompts**:
  * 💬 `"open github.com"`
  * 💬 `"open google.com"`

---

### 4.3 YouTube Video Search
* **Action Mapping**: `search_youtube`
* **Description**: Searches YouTube online and opens matching video results in the browser.
* **Example Prompts**:
  * 💬 `"play lofi on youtube"`
  * 💬 `"search youtube for python tutorials"`

---

## 5. 🛍️ Commerce Research & Price Comparison

Commands for multi-merchant product research, price comparison, and payment preview preparation.

### 5.1 Multi-Merchant Product Research
* **Action Mapping**: `commerce_research`
* **Description**: Conducts multi-merchant search across Amazon, Flipkart, Croma, compares offer prices, and verifies direct product page links.
* **Example Prompts**:
  * 💬 `"search for a todo book on all shopping platforms"`
  * 💬 `"find wireless keyboard under ₹2000"`
  * 💬 `"compare prices for Logitech K120 keyboard"`

---

### 5.2 Payment Intent Preparation
* **Action Mapping**: `prepare_payment`
* **Description**: Validates direct product page URL, checks `TransactionGuard` limits, and renders Payment Preview Card in UI requiring explicit user click authorization.
* **Example Prompts**:
  * 💬 `"prepare payment for Logitech keyboard"`
  * 💬 `"buy Logitech K120"`

---

## 6. 📝 Notes & Knowledge Base (Local RAG)

Commands for managing local text notes and retrieving knowledge from indexed documents.

### 6.1 Create Note
* **Action Mapping**: `create_note`
* **Description**: Saves a new text note into local storage (`data/notes/`).
* **Example Prompts**:
  * 💬 `"create note titled Meeting with content Discuss project architecture"`
  * 💬 `"save a note named Shopping List with milk and eggs"`

---

### 6.2 Read / List Notes
* **Action Mapping**: `read_note`
* **Description**: Retrieves note content from local storage.
* **Example Prompts**:
  * 💬 `"read note titled Meeting"`
  * 💬 `"show my notes"`

---

### 6.3 Local RAG Knowledge Search
* **Action Mapping**: `retrieve_sop`
* **Description**: Searches indexed local notes and documents to retrieve grounded knowledge snippets.
* **Example Prompts**:
  * 💬 `"find safety SOP in local notes"`
  * 💬 `"search local documents for maintenance procedure"`

---

## 7. ⏰ Reminders & Task Scheduling

Commands for setting background reminders and managing scheduled tasks.

### 7.1 Schedule Reminder
* **Action Mapping**: `schedule_task`
* **Description**: Schedules a background APScheduler timer job that pops up a chat notification when expired.
* **Example Prompts**:
  * 💬 `"remind me in 10 minutes to join meeting"`
  * 💬 `"set a reminder in 1 hour to check build"`

---

### 7.2 List Active Reminders
* **Action Mapping**: `list_tasks`
* **Description**: Lists all active scheduled background reminder tasks and task IDs.
* **Example Prompts**:
  * 💬 `"show my tasks"`
  * 💬 `"list reminders"`

---

### 7.3 Cancel Reminder
* **Action Mapping**: `cancel_task`
* **Description**: Cancels a scheduled task using its task ID.
* **Example Prompts**:
  * 💬 `"cancel task 4c8b327e"`

---

## 8. 📊 Spreadsheet Processing & Data Analytics

Commands for ingesting, filtering, and calculating metrics on tabular datasets.

### 8.1 Analyze Spreadsheet
* **Action Mapping**: `analyze_spreadsheet`
* **Description**: Ingests `.xlsx` or `.csv` files, filters rows, aggregates column values, and generates mathematical analytics summaries.
* **Example Prompts**:
  * 💬 `"analyze sales.xlsx"`
  * 💬 `"calculate total revenue in data.csv"`
  * 💬 `"show average score in marks.xlsx"`

---

## 9. 💻 Sandboxed Code Execution

Commands for executing Python code in isolated subprocesses.

### 9.1 Run Python Code
* **Action Mapping**: `run_sandbox_code`
* **Description**: Executes generated Python code inside an isolated sandbox subprocess with strict 5-second execution timeouts and secret masking.
* **Example Prompts**:
  * 💬 `"run this python calculation safely"`
  * 💬 `"execute script to compute prime numbers up to 100"`

---

## 10. 📧 Email & Communication

Commands for opening Gmail and preparing draft emails.

### 10.1 Compose Gmail Draft
* **Action Mapping**: `compose_gmail`
* **Description**: Opens a draft email window with pre-populated recipient address, subject, and generated message body.
* **Example Prompts**:
  * 💬 `"compose email to john@example.com with subject Meeting"`
  * 💬 `"send email to principal@gmail.com"`

---

### 10.2 Open Gmail Inbox
* **Action Mapping**: `open_gmail`
* **Description**: Opens `mail.google.com` in default web browser.
* **Example Prompts**:
  * 💬 `"open my gmail inbox"`

---

## 11. 🔧 System Diagnostics & Utilities

Commands for inspecting hardware telemetry, network status, and system maintenance.

### 11.1 System Information & Hardware Telemetry
* **Action Mapping**: `system_info` / `battery`
* **Description**: Reports active CPU load percentage, available RAM, battery charging status, and OS metadata.
* **Example Prompts**:
  * 💬 `"system info"`
  * 💬 `"show cpu and ram usage"`
  * 💬 `"battery status"`

---

### 11.2 IP Address & Running Processes
* **Action Mapping**: `ip_address` / `running_apps`
* **Description**: Reports local IP addresses and lists active non-system application processes.
* **Example Prompts**:
  * 💬 `"what is my ip address"`
  * 💬 `"what apps are running"`

---

### 11.3 Kill Application Process
* **Action Mapping**: `kill_app`
* **Description**: Force-closes matching process name (*Requires user confirmation*).
* **Example Prompts**:
  * 💬 `"close Chrome"`
  * 💬 `"kill notepad"`

---

### 11.4 System Maintenance (Flush DNS, Empty Recycle Bin)
* **Action Mapping**: `flush_dns` / `empty_recycle`
* **Description**: Flushes Windows DNS cache or empties the Windows Recycle Bin (*Requires confirmation*).
* **Example Prompts**:
  * 💬 `"flush dns"`
  * 💬 `"empty recycle bin"`

---

## 12. 🤖 Offline LLM & Model Control

Commands for listing, downloading, and switching AI reasoning models.

### 12.1 Ollama Local Model Control
* **Action Mapping**: `ollama_list` / `ollama_pull` / `ollama_delete`
* **Description**: Reports, pulls, or deletes local Ollama model layers.
* **Example Prompts**:
  * 💬 `"list ollama models"`
  * 💬 `"pull gemma3 model"`
  * 💬 `"delete model mistral"`

---

### 12.2 Switch Model Routing Mode
* **Action Mapping**: `set_model_mode`
* **Description**: Switches HELIOS routing mode between `AUTO`, `LOCAL` (gemma3), or `CLOUD` (`gemini-3.6-flash`).
* **Example Prompts**:
  * 💬 `"switch model to AUTO"`
  * 💬 `"use local model"`
  * 💬 `"switch to cloud model"`
