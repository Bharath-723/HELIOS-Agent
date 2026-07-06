from typing import Dict, Any

class GroundTruthEvaluator:
    @staticmethod
    def evaluate(expected: Dict[str, Any], observed: Dict[str, Any]) -> str:
        intent_match = expected["intent"] == observed["intent"]
        
        exp_route = expected["route"]
        obs_route = observed["route"]
        route_match = exp_route == obs_route
        
        if intent_match and route_match:
            return "PASS"
        elif intent_match or route_match:
            return "PARTIAL"
        else:
            return "FAIL"
