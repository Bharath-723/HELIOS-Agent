import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from core.routing.routing_models import RoutingContext, RoutingFeatures

log = logging.getLogger("helios.routing.feature_extractor")

class FeatureExtractor:
    def __init__(self, rules_path: Optional[str] = None):
        if rules_path is None:
            rules_path = str(Path(__file__).parent / "routing_rules.json")
            
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, rules_path: str) -> Dict[str, Any]:
        try:
            if os.path.exists(rules_path):
                with open(rules_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                log.warning("routing_rules.json not found at %s. Using default empty rules.", rules_path)
                return {}
        except Exception as exc:
            log.error("Failed to load routing rules: %s", exc, exc_info=True)
            return {}

    def extract(self, context: RoutingContext) -> RoutingFeatures:
        log.info("extract called for prompt='%s'", context.prompt)
        prompt_lower = context.prompt.lower()
        
        # Initialize default features
        features = RoutingFeatures()
        reasons = []

        # Deterministic keyword scanning based on rules config
        for category, config in self.rules.items():
            keywords = config.get("keywords", [])
            matched = [k for k in keywords if re.search(r'\b' + re.escape(k) + r'\b', prompt_lower)]
            
            if matched:
                reasons.append(f"Matched {category} keywords: {', '.join(matched)}")
                
                # Apply rules mappings
                if category == "privacy":
                    features.privacy_score = max(features.privacy_score, config.get("privacy_score", 0.0))
                    features.contains_sensitive_data = features.contains_sensitive_data or config.get("contains_sensitive_data", False)
                elif category == "freshness":
                    features.freshness_score = max(features.freshness_score, config.get("freshness_score", 0.0))
                    features.requires_internet = features.requires_internet or config.get("requires_internet", False)
                elif category == "local_data":
                    features.contains_local_data = features.contains_local_data or config.get("contains_local_data", False)
                    features.privacy_score = max(features.privacy_score, config.get("privacy_score", 0.0))
                elif category == "complexity":
                    features.complexity_score = max(features.complexity_score, config.get("complexity_score", 0.0))

        # Basic default estimates (non-AI stubs)
        features.estimated_tokens = len(context.prompt.split()) * 2
        features.estimated_execution = 0.5 + (0.1 * features.estimated_tokens)
        
        # Calculate mock scores
        if features.contains_sensitive_data:
            features.privacy_score = 0.95
        if features.requires_internet:
            features.freshness_score = 0.90
            
        features.hardware_score = 0.40  # default average
        features.latency_score = 0.50   # default average
        features.cost_score = 0.10 if features.requires_internet else 0.0
        
        features.reasoning = "; ".join(reasons) if reasons else "No keyword matches found. Defaulting to general baseline features."
        return features
