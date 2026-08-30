# HELIOS v1.0.1 Runtime Exceptions Log

| Component | Exception Scenario | Handler Behavior | Status |
| :--- | :--- | :--- | :--- |
| **Router** | ConnectionRefused (Ollama down) | Intercepts error, logs trace, returns fallback | **PASS** |
| **FileCreator** | PathTraversal (`../../`) | Validates and rejects parameters safely | **PASS** |
| **FileCreator** | Prohibited characters (`*?`) | Validates and rejects parameters safely | **PASS** |
| **WebSearch** | DDG Import Error | Tries duckduckgo_search, returns warning | **PASS** |
| **GmailComposer** | Webbrowser Launch Error | Catches browser exception and logs warning | **PASS** |
