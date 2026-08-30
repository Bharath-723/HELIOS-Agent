"""
core/network_audit.py — HELIOS Network Isolation & Audit Monitor
===================================================================
Local audit logger and security policy monitor.
Tracks cloud vs local model dispatches, domain endpoints, privacy scores, and latency.
Enforces strict secret masking: NEVER logs API keys, passwords, or document secrets.
"""

from __future__ import annotations
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

log = logging.getLogger("helios.network_audit")

AUDIT_LOG_PATH = Path(__file__).parent.parent / "data" / "logs" / "network_audit.jsonl"


class NetworkAuditMonitor:
    """Security audit logger for model routing and network access."""

    POLICY_LOCAL_ONLY = "LOCAL_ONLY"
    POLICY_CLOUD_ALLOWED = "CLOUD_ALLOWED"
    POLICY_CLOUD_FORBIDDEN = "CLOUD_FORBIDDEN"

    @staticmethod
    def _sanitize(data: Any) -> Any:
        if isinstance(data, dict):
            clean = {}
            for k, v in data.items():
                if any(sec in str(k).lower() for sec in ["key", "secret", "password", "token", "auth", "credential"]):
                    clean[k] = "[REDACTED_SECRET]"
                else:
                    clean[k] = NetworkAuditMonitor._sanitize(v)
            return clean
        elif isinstance(data, list):
            return [NetworkAuditMonitor._sanitize(x) for x in data]
        elif isinstance(data, str):
            if "sk-or-v1-" in data or "AIzaSy" in data or "Bearer " in data:
                return "[REDACTED_SECRET_TOKEN]"
        return data

    @classmethod
    def log_event(
        cls,
        provider_name: str,
        endpoint_domain: str,
        decision_mode: str,  # "LOCAL" or "CLOUD"
        selected_model: str,
        policy: str = POLICY_LOCAL_ONLY,
        latency_ms: float = 0.0,
        success: bool = True,
        privacy_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider_name,
            "domain": endpoint_domain,
            "decision": decision_mode,
            "selected_model": selected_model,
            "policy": policy,
            "privacy_score": privacy_score,
            "latency_ms": round(latency_ms, 2),
            "success": success,
            "metadata": cls._sanitize(metadata or {})
        }

        log.info("Network Audit Logged: [%s] Provider=%s Model=%s Latency=%.2fms",
                 decision_mode, provider_name, selected_model, latency_ms)

        try:
            AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as exc:
            log.error("Failed to write network audit log: %s", exc)

        return event
