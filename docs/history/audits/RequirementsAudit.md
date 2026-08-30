# HELIOS v3.5 — Requirements Audit
**Phase 2: Production Hardening**

---

## 1. Cleaned Requirements Specification (`requirements.txt`)

`requirements.txt` was cleaned to contain strictly used, active packages with upper and lower version bounds for Windows 10/11 compatibility:

```requirements
ollama>=0.1.8,<=0.4.7
openai>=1.30.0,<=1.58.0
google-genai>=1.0.0,<=1.2.0
requests>=2.31.0,<=2.32.3
duckduckgo-search>=6.1.0,<=7.2.1
apscheduler>=3.10.4,<=3.11.0
pyautogui>=0.9.54
pygetwindow>=0.0.9
plyer>=2.1.0
python-docx>=1.1.0,<=1.1.2
reportlab>=4.1.0,<=4.2.5
psutil>=5.9.8,<=6.1.1
rich>=13.7.0,<=13.9.4
python-dotenv>=1.0.1
SpeechRecognition>=3.8.1,<=3.14.1
pyaudio>=0.2.11,<=0.2.14
wmi>=1.5.1
pywin32>=306
tzlocal>=5.1
```

---

## 2. Purged Unused Dependencies

The following 7 unused bloated dependencies were purged from `requirements.txt`:
1. `streamlit` (~150MB)
2. `pyperclip` (replaced by tkinter clipboard API)
3. `openpyxl`
4. `pandas` (~100MB)
5. `beautifulsoup4`
6. `schedule` (replaced by `apscheduler`)
7. `pipwin`

---

## 3. Added Required Dependencies
1. `wmi`: Required for Windows hardware diagnostics in `ui/diagnostics_panel.py`.
2. `pywin32`: Required for Windows registry and OS system queries.
3. `tzlocal`: Required for dynamic local system timezone detection.

---

## 4. Generated Lockfiles
- `requirements.lock`: Lockfile pinning exact package versions for reproducible installation.
- `requirements-dev.txt`: Tooling dependencies (`pytest`, `flake8`, `mypy`) for development environments.
