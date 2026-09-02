# Changelog

All notable changes to the HELIOS project are documented in this file.

## [v1.0.1] - 2026-07-05
### Added
- Centralized path containment helper (`_is_contained`) using `Path.resolve()` and `is_relative_to()`.
- Windows invalid character validation (`< > : " / \ | ? *`) on filenames in `FileCreator`, `_move_file`, and `_delete_file`.
- Input validation sanitizers to prevent PowerShell command injections in DesktopAgent query fallbacks.
- Missing dependencies `reportlab` and `pygetwindow` added to `requirements.txt`.
- Comprehensive release manifests (`RELEASE.md` and `KNOWN_LIMITATIONS.md`).

### Fixed
- Relocated files, database directories (`scheduled_tasks.json`, `.index.json`, chat files), and log files (`helios.log`) to resolve absolutely relative to the project root, resolving runtime directory fragmentation.
- Bypassed npx interactive queries using `--yes` flag to prevent command-line execution freezes.
- Replaced direct `int()` string casts with `_safe_int()` parameters wrapper inside `HELIOSAgent` to prevent dispatcher conversion crashes.

## [v1.0.0] - 2026-07-05
### Added
- Setup local-first LLM routing and database configuration scripts.
- Replaced print debug statement lines with Python `logging` trace operations.
- Added lazy-loading imports for heavy PDF libraries to avoid startup dependency checks.
