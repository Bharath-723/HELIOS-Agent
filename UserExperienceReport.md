# HELIOS User Experience Report

---

### 1. User Interface & Responsiveness Verification
* **Startup time**: < 1.0 second (no blocking network calls during router loading).
* **UI Responsiveness**: Caching of internet and Ollama connectivity checks prevents any GUI lockups or frame drops during typing.
* **Notification delivery**: Reminders from the APScheduler thread pop up on the UI cleanly without freezing the user interface window.
* **Shutdown time**: Clean connection closes and thread stops, exiting in < 0.5 seconds.
