import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from core.routing.routing_models import RoutingContext, RoutingFeatures

log = logging.getLogger("helios.routing.score_engine")

class ScoreEngine:
    def __init__(self, weights_path: Optional[str] = None):
        if weights_path is None:
            weights_path = str(Path(__file__).parent / "routing_weights.json")
            
        config = self._load_config(weights_path)
        self.weights = config.get("weights", {})
        self.capabilities = config.get("capabilities", {})

    def _load_config(self, weights_path: str) -> Dict[str, Any]:
        try:
            if os.path.exists(weights_path):
                with open(weights_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                log.warning("routing_weights.json not found at %s. Using default configs.", weights_path)
                return {}
        except Exception as exc:
            log.error("Failed to load routing weights config: %s", exc, exc_info=True)
            return {}

    def calculate_local_utility(self, context: RoutingContext, features: RoutingFeatures) -> float:
        w = self.weights
        wp = w.get("privacy", 0.35)
        wf = w.get("freshness", 0.15)
        wcx = w.get("complexity", 0.25)
        wl = w.get("latency", 0.15)
        wc = w.get("cost", 0.10)

        cap = self.capabilities.get("local", {})
        c_p = cap.get("privacy_capability", 1.0)
        c_f = cap.get("freshness_capability", 0.0)
        c_cx = cap.get("complexity_capability", 0.6)
        c_l = cap.get("latency_capability", 0.8)
        c_c = cap.get("cost_capability", 1.0)

        r_p = features.privacy_score
        r_f = features.freshness_score
        r_cx = features.complexity_score

        s_p = (c_p * r_p) + (1.0 - r_p)
        s_f = c_f * r_f
        s_cx = c_cx * r_cx
        s_l = c_l
        s_c = c_c

        utility = (wp * s_p) + (wf * s_f) + (wcx * s_cx) + (wl * s_l) + (wc * s_c)
        log.info("Local Utility score calculated: %f", utility)
        return utility

    def calculate_cloud_utility(self, context: RoutingContext, features: RoutingFeatures) -> float:
        w = self.weights
        wp = w.get("privacy", 0.35)
        wf = w.get("freshness", 0.15)
        wcx = w.get("complexity", 0.25)
        wl = w.get("latency", 0.15)
        wc = w.get("cost", 0.10)

        cap = self.capabilities.get("cloud", {})
        c_p = cap.get("privacy_capability", 0.3)
        c_f = cap.get("freshness_capability", 1.0)
        c_cx = cap.get("complexity_capability", 0.95)
        c_l = cap.get("latency_capability", 0.5)
        c_c = cap.get("cost_capability", 0.2)

        r_p = features.privacy_score
        r_f = features.freshness_score
        r_cx = features.complexity_score

        s_p = (c_p * r_p) + (1.0 - r_p)
        s_f = c_f * r_f
        s_cx = c_cx * r_cx
        s_l = c_l
        s_c = c_c

        utility = (wp * s_p) + (wf * s_f) + (wcx * s_cx) + (wl * s_l) + (wc * s_c)
        log.info("Cloud Utility score calculated: %f", utility)
        return utility

    def evaluate_scores(self, context: RoutingContext, features: RoutingFeatures) -> Dict[str, float]:
        local_score = self.calculate_local_utility(context, features)
        cloud_score = self.calculate_cloud_utility(context, features)
        return {
            "local_utility": local_score,
            "cloud_utility": cloud_score
        }
