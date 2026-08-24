# HELIOS v2: Planning Engine Validation Report

This report summarizes the execution outcomes of the Cognitive Planning Engine validation suite (`reasoning_validation.py`).

---

## 1. Test Summary
- **Tests Executed**: 6 core workflow scenarios
- **Context States Evaluated**: Online (Standard), Offline (Internet constrained), Low RAM (Resource constrained)
- **Status**: **100% PASS**

---

## 2. Test Execution Details

### 2.1 Simple Chat
- *Prompt*: `"Hi, tell me a short story about antigravity."`
- *Category*: CHAT
- *Tasks*: 1
- *State*: PASS (Routed locally via gemma3, latency scaled under low RAM context)

### 2.2 Web Search
- *Prompt*: `"Search online for the latest news about Space Exploration."`
- *Category*: SEARCH
- *Tasks*: 3 (Order: Connectivity check -> DDG Search -> Summarize)
- *State*: PASS (Requires internet. Offline context correctly triggered local model fallback and escalated risk to 0.90)

### 2.3 File Creation
- *Prompt*: `"Create a file named resume_template.docx with basic sections."`
- *Category*: FILE
- *Tasks*: 2 (Time parsing -> DesktopAgent file creation)
- *State*: PASS (Privacy categorized as medium, no internet required)

### 2.4 Scheduling
- *Prompt*: `"Schedule a reminder in 15 minutes to pay college fees."`
- *Category*: SCHEDULE
- *Tasks*: 2 (Parse trigger time -> Register TaskScheduler job)
- *State*: PASS (Topologically sorted order verified)

### 2.5 Privacy Task
- *Prompt*: `"Here is my bank personal password: secret123, keep it safe."`
- *Category*: PRIVACY_TASK
- *Tasks*: 1 (Offline gemma3 processing)
- *State*: PASS (Privacy escalated to high, internet flag is False)

### 2.6 Mixed / Multi-step Workflow
- *Prompt*: `"Search online for the latest news about Python 3.12 and save note to my notes folder."`
- *Category*: MIXED
- *Tasks*: 4 (Order: Connectivity -> WebSearch -> Summarize -> NotesManager note saving)
- *State*: PASS (Mixed workflow logic splits goals, escalates privacy to medium because of notes saving, and validates parallel grouping levels)
