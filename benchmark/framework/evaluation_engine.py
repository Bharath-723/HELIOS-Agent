from typing import List, Dict, Any
from benchmark.framework.ground_truth_evaluator import GroundTruthEvaluator

class EvaluationEngine:
    def __init__(self):
        self.evaluator = GroundTruthEvaluator()

    def evaluate_run(self, expected_prompts: List[Any], results: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(results)
        passed = 0
        partial = 0
        failed = 0
        
        for exp, obs in zip(expected_prompts, results):
            exp_dict = {
                "intent": exp.expected_intent,
                "route": exp.expected_route
            }
            obs_dict = {
                "intent": obs["observed_intent"],
                "route": obs["observed_route"]
            }
            verdict = self.evaluator.evaluate(exp_dict, obs_dict)
            if verdict == "PASS":
                passed += 1
            elif verdict == "PARTIAL":
                partial += 1
            else:
                failed += 1
                
        return {
            "total_runs": total,
            "pass_count": passed,
            "partial_count": partial,
            "fail_count": failed,
            "accuracy": (passed / total) if total > 0 else 0.0
        }
