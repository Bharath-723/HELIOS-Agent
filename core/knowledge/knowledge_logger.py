"""
HELIOS v2 - Knowledge Logger
Outputs structured telemetry events for knowledge, memory caching, and retrieval operations.
"""
import json
import logging
from typing import Dict, Any

log = logging.getLogger("helios.knowledge.logger")

class KnowledgeLogger:
    def log_event(self, event_type: str, details: Dict[str, Any]):
        log_payload = {
            "event_type": event_type,
            "details": details
        }
        log.info("Knowledge Event Trace: %s", json.dumps(log_payload, ensure_ascii=False))

    def log_cache_hit(self, key: str, access_count: int):
        self.log_event("cache_hit", {"cache_key": key, "access_count": access_count})

    def log_memory_lookup(self, query_summary: Dict[str, Any], results_count: int):
        self.log_event("memory_lookup", {"query": query_summary, "results_count": results_count})

    def log_graph_modification(self, action: str, node_or_edge_id: str):
        self.log_event("graph_modification", {"action": action, "target_id": node_or_edge_id})
