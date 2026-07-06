# Known Limitations

This document lists the technical boundaries and constraints of the **HELIOS v1.0.1** research baseline. These limitations are intentional to maintain a stable baseline profile.

1. **Windows-Specific Automation**: Desktop controls, brightness toggles, volume settings, app launching, and PowerShell commands rely strictly on Windows Win32 APIs, ctypes, and PowerShell environments. Cross-platform execution (macOS/Linux) is not supported for desktop automations.
2. **Local Inference Dependence**: Local LLM routing relies on an active, running instance of Ollama on `http://localhost:11434`. If Ollama is stopped or the model is not pulled, router requests fallback to direct general chat responses.
3. **Cloud API Network Dependence**: Live external services like Gmail composition prompts, search indices via DuckDuckGo, and cloud LLMs require active internet connections.
4. **No Adaptive Routing**: Query routing is determined statically by NLRouter formatting parameters passed to the LLM engine. Dynamic or self-optimizing route adapters are not implemented.
5. **No Vector Database / RAG**: Notes and document structures are indexed inside simple flat JSON structures (`.index.json`). Semantic or vector search embeddings are not present.
6. **Short-Term Context Only**: Chat transcripts are appended to individual session JSON files, and only the immediate recent message window is used for context. There is no long-term memory system.
7. **Subprocess Performance**: System checks, Wi-Fi queries, and night light status actions launch synchronous powershell commands, which may introduce 1–2 second delays depending on system resources.
