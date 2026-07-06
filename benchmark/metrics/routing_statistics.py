class RoutingStatistics:
    def __init__(self):
        self.route_counts = {"LOCAL": 0, "CLOUD": 0}
        self.model_counts = {}
        self.confidence_values = []

    def log_decision(self, route: str, model: str, confidence: float):
        self.route_counts[route] = self.route_counts.get(route, 0) + 1
        self.model_counts[model] = self.model_counts.get(model, 0) + 1
        self.confidence_values.append(confidence)

    def get_summary(self) -> dict:
        avg_conf = sum(self.confidence_values) / len(self.confidence_values) if self.confidence_values else 0.0
        return {
            "route_counts": self.route_counts,
            "model_counts": self.model_counts,
            "average_confidence": avg_conf
        }
