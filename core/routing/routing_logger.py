import json
import logging
from datetime import datetime
from pathlib import Path
from core.routing.routing_models import RoutingResult

log = logging.getLogger("helios.routing.logger")

class RoutingLogger:
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(__file__).parent.parent.parent / log_dir
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            log.error("Failed to create routing log directory: %s", exc)

    def log_route(self, result: RoutingResult):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": result.context.prompt,
            "intent": result.context.parsed_intent,
            "routing_features": {
                "privacy_score": result.features.privacy_score,
                "freshness_score": result.features.freshness_score,
                "complexity_score": result.features.complexity_score,
                "requires_internet": result.features.requires_internet,
                "contains_local_data": result.features.contains_local_data,
                "contains_sensitive_data": result.features.contains_sensitive_data
            },
            "constraint_result": result.constraints_triggered,
            "local_score": result.scores.get("local_utility", 0.0),
            "cloud_score": result.scores.get("cloud_utility", 0.0),
            "decision": result.decision.value,
            "selected_model": result.selected_model,
            "execution_time_ms": result.execution_time_ms
        }
        
        log.info("Routing Event Trace: %s", json.dumps(log_entry))
        
        log_file = self.log_dir / "routing_traces.jsonl"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as exc:
            log.error("Failed to write structured route trace to log file: %s", exc)
