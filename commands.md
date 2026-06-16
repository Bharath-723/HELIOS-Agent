# 📋 HELIOS Command Reference Guide

This document contains the complete list of natural language commands, parameters, and actions executable by the HELIOS agent.

---

## 📄 File & Document Operations

| Feature | Prompt Pattern Examples | Action/Parameter Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Convert to PDF** | `"convert essay.txt to pdf"`<br>`"make a pdf of resume.docx"`<br>`"text file into a pdf"` | `convert_to_pdf`<br>`query="filename"` | Finds txt or docx file on system, compiles to PDF, and launches in default viewer. |
| **Create File** | `"create file note.txt on desktop"` | `create_file`<br>`name="note.txt"`, `location="desktop"` | Creates empty or pre-filled file on Desktop or Documents. |
| **Search/Find File** | `"search for tax in my local pc"` | `find_file`<br>`query="tax"` | Performs recursive search inside user profile directories. |
| **List Folder** | `"list files in downloads"` | `list_folder`<br>`location="downloads"` | Lists files in Desktop, Documents, Downloads, Music, Pictures, or Videos. |
| **Search in File** | `"find python in notes.txt"` | `search_in_file`<br>`filename="notes.txt"`, `keyword="python"` | Scans lines inside a specific file to locate occurrences of a keyword. |
| **Move File** | `"move report.pdf from desktop to documents"` | `move_file`<br>`name="report.pdf"`, `from="desktop"`, `to="documents"` | Moves a file between home directory subfolders. |
| **Delete File** | `"delete draft.txt"` | `delete_file`<br>`name="draft.txt"` | Removes a file permanently from disk. |

---

## 🖥️ Direct System Controls

| Feature | Prompt Pattern Examples | Action/Parameter Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Night Light** | `"turn on night light"`<br>`"turn off night light"`<br>`"is night light on"` | `night_light_on`<br>`night_light_off`<br>`night_light_status` | Silently controls display color temperature via `nightlight-cli` (no Settings app redirect). |
| **Energy Saver** | `"turn on energy saver"`<br>`"turn off energy saver"`<br>`"battery saver mode"` | `power_saver`<br>`power_balanced`<br>`power_saver` | Direct power scheme override (SCHEME_MAX for Power Saver, SCHEME_BALANCED for Balanced). |
| **Mobile Hotspot** | `"turn on mobile hotspot"`<br>`"turn off mobile hotspot"`<br>`"hotspot status"` | `hotspot_on`<br>`hotspot_off`<br>`hotspot_status` | Manages hotspot adapter programmatically via WinRT `NetworkOperatorTetheringManager` APIs. |
| **Wi-Fi** | `"turn off wifi"`<br>`"turn on wifi"`<br>`"wifi status"` | `wifi_on`<br>`wifi_off`<br>`wifi_status` | Manages Wi-Fi adapter. Includes Windows elevation/UAC consent warning popups. |
| **Bluetooth** | `"turn on bluetooth"`<br>`"turn off bluetooth"` | `bluetooth_on`<br>`bluetooth_off` | Direct device status control using WinRT Radio APIs. |
| **Airplane Mode** | `"turn on airplane mode"`<br>`"turn off airplane mode"` | `airplane_mode_on`<br>`airplane_mode_off` | Programmatic radio override (toggles Wi-Fi and Bluetooth simultaneously). |
| **Dark Mode** | `"turn on dark mode"`<br>`"turn off dark mode"` | `dark_mode_on`<br>`dark_mode_off` | Updates Windows registry personalization keys to toggle dark theme. |
| **Brightness** | `"set brightness to 50"`<br>`"brightness up"`<br>`"dim screen"` | `brightness_set`<br>`brightness_up`<br>`brightness_down` | Sets screen brightness levels programmatically (laptops/compatible monitors). |

---

## 🎵 Media & Browsing

| Feature | Prompt Pattern Examples | Action/Parameter Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Play Media** | `"play spiderman video from local pc"` | `play_media`<br>`query="spiderman"` | Searches video/audio folders on PC and plays choice in default player. |
| **Search YouTube** | `"play lofi on youtube"` | `search_youtube`<br>`query="lofi"` | Searches YouTube online and opens browser directly. |
| **Playback Control** | `"pause the video"` | `pause_media` | Simulates global media key press to pause/resume play. |
| **Close Media** | `"stop playing both videos"`<br>`"close youtube"` | `stop_media` | Closes active YouTube tabs/windows in Chrome and sends stop signal. |
| **Open Website** | `"open github"` | `open_website`<br>`site="github.com"` | Launches specified site directly in default browser. |
| **Web Search** | `"search for python tutorials on Google"` | `search_google`<br>`query="tutorials"` | Performs search query on Google. |

---

## 📧 Productivity & Organization

| Feature | Prompt Pattern Examples | Action/Parameter Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Gmail Compose** | `"compose mail to principal@gmail.com"` | `compose_gmail`<br>`to="principal@gmail.com"` | Opens draft window with populated address, subject, and generated body. |
| **Open Gmail** | `"open my gmail inbox"` | `open_gmail` | Opens `mail.google.com` in browser. |
| **Reminders** | `"remind me in 10 minutes to join meeting"` | `schedule_task`<br>`description="join meeting"`, `time="10 mins"` | Adds background APScheduler job that pops up chat reminder notification. |
| **Task Lists** | `"show my tasks"` | `list_tasks` | Prints all active background reminders and IDs. |
| **Cancel Task** | `"cancel task 4c8b327e"` | `cancel_task`<br>`id="4c8b327e"` | Removes scheduled reminder from job store. |
| **Note Taking** | `"create note about shopping list"` | `create_note`<br>`title="shopping list"`, `content=""` | Saves note to local database file. |
| **Read Notes** | `"read note about shopping list"` | `read_note`<br>`title="shopping list"` | Retrieves content of local note. |

---

## 🛠️ Diagnostics & Utilities

| Feature | Prompt Pattern Examples | Action/Parameter Mapping | Description |
| :--- | :--- | :--- | :--- |
| **System Info** | `"system info"` | `system_info` | Displays CPU stats, RAM usage, storage space, and OS version. |
| **Battery Status** | `"battery status"` | `battery` | Checks charging state and battery percentage. |
| **Volume Control** | `"volume up"`, `"volume down"`, `"mute"` | `volume_up`<br>`volume_down`<br>`mute` | Simulates global volume key events. |
| **Apps Running** | `"what apps are running"` | `running_apps` | Lists active process names (excludes standard system services). |
| **Kill Process** | `"close Chrome"`, `"kill notepad"` | `kill_app`<br>`app="Chrome"` | Force-closes matching process name. *Requires confirmation*. |
| **Diagnostics** | `"flush dns"` | `flush_dns` | Performs network cache flush. |
| **IP Address** | `"what is my ip address"` | `ip_address` | Reports local host IP and active interface addresses. |
| **Clean Storage** | `"empty recycle bin"` | `empty_recycle` | Programmatically empties Recycle Bin. *Requires confirmation*. |

---

## 🤖 Offline LLM Control (Ollama)

| Feature | Prompt Pattern Examples | Action/Parameter Mapping | Description |
| :--- | :--- | :--- | :--- |
| **List Models** | `"list ollama models"` | `ollama_list` | Reports all models cached/installed locally. |
| **Download Model** | `"pull gemma3 model"` | `ollama_pull`<br>`model="gemma3"` | Pulls model directly from Ollama registry in background. |
| **Delete Model** | `"delete model mistral"` | `ollama_delete`<br>`model="mistral"` | Deletes local cached model layers. |
