import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from core.routing.routing_models import RoutingContext

log = logging.getLogger("helios.routing.candidate_manager")

class CandidateManager:
    def __init__(self, capabilities_path: str = None):  # type: ignore
        if capabilities_path is None:
            capabilities_path = str(Path(__file__).parent / "routing_capabilities.json")
            
        self.profiles = self._load_profiles(capabilities_path)

    def _load_profiles(self, path: str) -> Dict[str, Any]:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                log.warning("Capabilities file not found at %s. Using default profile map.", path)
                return {}
        except Exception as exc:
            log.error("Failed to load capabilities profiles: %s", exc)
            return {}

    def get_available_candidates(self, context: RoutingContext) -> List[str]:
        candidates = []
        for model_name, profile in self.profiles.items():
            model_type = profile.get("type", "local")
            if model_type == "local":
                if context.local_model_available:
                    candidates.append(model_name)
            elif model_type == "cloud":
                if context.cloud_available and context.internet_available:
                    candidates.append(model_name)
                    
        log.info("Available candidate models found: %s", candidates)
        return candidates
