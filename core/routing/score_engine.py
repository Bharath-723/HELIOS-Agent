import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from core.routing.routing_models import RoutingContext, RoutingFeatures

log = logging.getLogger("helios.routing.score_engine")

class ScoreEngine:
    def __init__(self, weights_path: Optional[str] = None, capabilities_path: Optional[str] = None):
        if weights_path is None:
            weights_path = str(Path(__file__).parent / "routing_weights.json")
        if capabilities_path is None:
            capabilities_path = str(Path(__file__).parent / "routing_capabilities.json")
            
        self.weights = self._load_config(weights_path).get("weights", {})
        self.capabilities = self._load_capabilities(capabilities_path)
        
        self.validate_weights()

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

    def _load_capabilities(self, capabilities_path: str) -> Dict[str, Any]:
        try:
            if os.path.exists(capabilities_path):
                with open(capabilities_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                log.warning("routing_capabilities.json not found at %s. Using default empty capabilities.", capabilities_path)
                return {}
        except Exception as exc:
            log.error("Failed to load routing capabilities: %s", exc, exc_info=True)
            return {}

    def validate_weights(self) -> None:
        required_keys = ["privacy", "freshness", "complexity", "latency", "cost"]
        
        for key in required_keys:
            if key not in self.weights:
                raise ValueError(f"Weight validation failed: missing key '{key}'")
                
            val = self.weights[key]
            if not isinstance(val, (int, float)):
                raise TypeError(f"Weight validation failed: key '{key}' has non-numeric value '{val}'")
                
            if val < 0.0:
                raise ValueError(f"Weight validation failed: key '{key}' has negative value {val}")
                
        total = sum(self.weights[k] for k in required_keys)
        if abs(total - 1.0) > 1e-5:
            raise ValueError(f"Weight validation failed: weights sum to {total}, expected 1.0 (tolerance 1e-5)")

    def get_effective_capability(self, model_name: str, context: RoutingContext, verbose: bool = True) -> Dict[str, float]:
        static_cap = self.capabilities.get(model_name, {}).copy()
        if not static_cap:
            if verbose:
                log.warning("Model profile '%s' not found. Using zero capability stubs.", model_name)
            return {
                "privacy": 0.0, "freshness": 0.0, "complexity": 0.0,
                "latency": 0.0, "cost": 0.0, "type": "local"
            }
            
        model_type = static_cap.get("type", "local")
        
        eff = {
            "privacy": static_cap.get("privacy", 0.0),
            "freshness": static_cap.get("freshness", 0.0),
            "complexity": static_cap.get("complexity", 0.0),
            "latency": static_cap.get("latency", 0.0),
            "cost": static_cap.get("cost", 0.0),
            "type": model_type
        }
        
        if model_type == "local":
            if not context.local_model_available:
                if verbose:
                    log.info("Adjustment: Local model unavailable. Effective capability of '%s' set to zero.", model_name)
                for key in ["privacy", "freshness", "complexity", "latency", "cost"]:
                    eff[key] = 0.0
                return eff
                
            if 0 < context.ram_available_mb < 4000.0:
                if verbose:
                    log.info("Adjustment: Low RAM (%f MB). Reducing complexity capability of '%s' by 30%%.", context.ram_available_mb, model_name)
                eff["complexity"] *= 0.70
                
            if not context.gpu_available:
                if verbose:
                    log.info("Adjustment: GPU unavailable. Reducing latency capability of '%s' by 40%%.", model_name)
                eff["latency"] *= 0.60
                
        elif model_type == "cloud":
            if not context.cloud_available:
                if verbose:
                    log.info("Adjustment: Cloud provider unavailable. Effective capability of '%s' set to zero.", model_name)
                for key in ["privacy", "freshness", "complexity", "latency", "cost"]:
                    eff[key] = 0.0
                return eff
                
        return eff

    def evaluate_model_utility(self, model_name: str, context: RoutingContext, features: RoutingFeatures) -> Dict[str, Any]:
        w = self.weights
        wp = w.get("privacy", 0.35)
        wf = w.get("freshness", 0.15)
        wcx = w.get("complexity", 0.25)
        wl = w.get("latency", 0.15)
        wc = w.get("cost", 0.10)

        cap = self.get_effective_capability(model_name, context, verbose=True)
        c_p = cap["privacy"]
        c_f = cap["freshness"]
        c_cx = cap["complexity"]
        c_l = cap["latency"]
        c_c = cap["cost"]

        r_p = features.privacy_score
        r_f = features.freshness_score
        r_cx = features.complexity_score

        s_p = (c_p * r_p) + (1.0 - r_p)
        s_f = c_f * r_f
        s_cx = c_cx * r_cx
        s_l = c_l
        s_c = c_c

        contrib_p = wp * s_p
        contrib_f = wf * s_f
        contrib_cx = wcx * s_cx
        contrib_l = wl * s_l
        contrib_c = wc * s_c

        total_utility = contrib_p + contrib_f + contrib_cx + contrib_l + contrib_c

        # Additive Capability Tag Match Evaluation (Phase 1A)
        static_cap = self.capabilities.get(model_name, {})
        model_caps = set(static_cap.get("capabilities", []))
        if model_caps:
            # Check if features require specific capability tags
            req_caps = set()
            if getattr(features, "requires_internet", False) and getattr(features, "freshness_score", 0.0) > 0.8:
                req_caps.add("web_search")
            if getattr(features, "requires_coding", False):
                req_caps.add("coding")
            if getattr(features, "requires_vision", False):
                req_caps.add("vision")
            
            # If required capability is present, add small capability boost (+0.05)
            if req_caps:
                matched = req_caps.intersection(model_caps)
                if matched:
                    total_utility += 0.05 * len(matched)
                elif "vision" in req_caps and "vision" not in model_caps:
                    # Incapable of requested vision feature
                    total_utility *= 0.50

        return {
            "total_utility": total_utility,
            "breakdown": {
                "privacy_contribution": contrib_p,
                "freshness_contribution": contrib_f,
                "complexity_contribution": contrib_cx,
                "latency_contribution": contrib_l,
                "cost_contribution": contrib_c
            }
        }
