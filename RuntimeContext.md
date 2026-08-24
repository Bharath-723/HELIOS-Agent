# HELIOS v3.5 — RuntimeContext Specification
**Phase 2: Production Hardening**

---

## 1. Overview

`RuntimeContext` (`core/system/runtime_manager.py`) is the immutable data structure exposed to application modules. It encapsulates the full environment, path hierarchy, system platform state, dependency statuses, and capability flags.

---

## 2. Structure Specification

```python
@dataclass
class RuntimeContext:
    version: VersionManager
    platform: PlatformManager
    paths: PathsManager
    environment: EnvironmentManager
    dependencies: DependencyStatus
    migration_completed: bool
    startup_ok: bool
    capabilities: dict
```

---

## 3. Key Capabilities Flags (`context.capabilities`)

- `is_windows`: `bool`
- `supports_gpu`: `bool`
- `supports_voice`: `bool`
- `ollama_available`: `bool`
- `internet_available`: `bool`
- `local_models`: `list[str]`
- `mode`: `str` ("offline", "online", "auto")
