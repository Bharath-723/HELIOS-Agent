# HELIOS v3.5 — Platform Abstraction Report
**Phase 2: Production Hardening**

---

## 1. Overview

`PlatformManager` (`core/system/platform.py`) isolates all OS-specific API calls, system directory lookups, registry queries, theme checks, and hardware queries behind an abstracted interface.

---

## 2. Abstracted Platform Helpers

- `is_windows()`: True on Windows systems (`sys.platform.startswith("win")`).
- `is_linux()`: True on Linux systems.
- `is_macos()`: True on macOS systems.
- `supports_gpu()`: Queries NVIDIA GPU capabilities via `nvidia-smi`.
- `supports_ollama()`: Validates Ollama IPC capabilities.
- `supports_voice()`: Validates PyAudio and SpeechRecognition availability.
- `get_system_theme()`: Reads Windows Registry (`AppsUseLightTheme`) on Windows, returns `dark` on other OS.
- `get_system_timezone()`: Queries system local timezone dynamically via `tzlocal`.
