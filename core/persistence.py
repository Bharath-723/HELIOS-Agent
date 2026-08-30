"""
core/persistence.py — HELIOS Persistence & Observability Manager
==================================================================
Manages structured persistence for CAHRA routing event logs, task execution traces,
action verification history, and safe non-blocking log rotation.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from core.system import paths_manager

log = logging.getLogger("helios.persistence")

DIAG_DIR = paths_manager.notes_dir.parent / "diagnostics"
try:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
except Exception as exc:
    log.error("Failed to create diagnostics directory %s: %s", DIAG_DIR, exc)

ROUTING_TRACE_LOG = DIAG_DIR / "cahra_routing_log.jsonl"
TASK_TRACE_LOG = DIAG_DIR / "task_execution_log.jsonl"


class PersistenceManager:
    """Observability and structured trace persistence manager."""

    @staticmethod
    def log_routing_event(event_dict: Dict[str, Any]) -> None:
        try:
            event_dict["recorded_at"] = datetime.now().isoformat()
            line = json.dumps(event_dict, ensure_ascii=False) + "\n"
            with open(ROUTING_TRACE_LOG, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as exc:
            log.warning("Failed to persist CAHRA routing trace: %s", exc)

    @staticmethod
    def log_task_execution(task_dict: Dict[str, Any]) -> None:
        try:
            task_dict["recorded_at"] = datetime.now().isoformat()
            line = json.dumps(task_dict, ensure_ascii=False) + "\n"
            with open(TASK_TRACE_LOG, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as exc:
            log.warning("Failed to persist task execution trace: %s", exc)

    @staticmethod
    def rotate_runtime_log_if_needed(log_path: str = "helios.log", max_bytes: int = 10 * 1024 * 1024) -> None:
        """Safely rotates runtime log if size exceeds limit."""
        p = Path(log_path)
        if not p.exists():
            return
        try:
            if p.stat().st_size > max_bytes:
                backup = p.with_name(p.name + ".1")
                if backup.exists():
                    backup.unlink()
                p.rename(backup)
                log.info("Rotated runtime log %s to %s", p.name, backup.name)
        except Exception as exc:
            log.warning("Could not rotate log %s: %s", p.name, exc)
