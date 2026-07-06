import logging
from typing import Dict
from core.routing.routing_models import RoutingContext, RoutingFeatures

log = logging.getLogger("helios.routing.score_engine")

class ScoreEngine:
    def calculate_local_utility(self, context: RoutingContext, features: RoutingFeatures) -> float:
        log.debug("calculate_local_utility called")
        return 0.5

    def calculate_cloud_utility(self, context: RoutingContext, features: RoutingFeatures) -> float:
        log.debug("calculate_cloud_utility called")
        return 0.5

    def evaluate_scores(self, context: RoutingContext, features: RoutingFeatures) -> Dict[str, float]:
        local_score = self.calculate_local_utility(context, features)
        cloud_score = self.calculate_cloud_utility(context, features)
        return {
            "local_utility": local_score,
            "cloud_utility": cloud_score
        }
