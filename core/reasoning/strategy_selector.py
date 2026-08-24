"""
HELIOS v2 - Strategy Selector
Selects the optimal strategy, generates selections and rejections explanations, and computes confidence margins.
"""
from typing import List, Dict, Any
from core.reasoning.reasoning_models import PlanningStrategy, SelectionDecision

class StrategySelector:
    def select(self, ranked_strategies: List[PlanningStrategy]) -> SelectionDecision:
        if not ranked_strategies:
            raise ValueError("No strategies available for selection.")

        selected = ranked_strategies[0]
        
        # 1. Compute selection table and margin
        ranking_table = []
        for rank, s in enumerate(ranked_strategies, 1):
            ranking_table.append({
                "rank": rank,
                "name": s.name,
                "policy": s.policy.value,
                "utility": s.evaluation_metrics.utility_score,
                "cost": s.evaluation_metrics.cost,
                "latency": s.evaluation_metrics.latency
            })

        margin = 0.0
        if len(ranked_strategies) > 1:
            margin = round(selected.evaluation_metrics.utility_score - ranked_strategies[1].evaluation_metrics.utility_score, 4)

        # Confidence: ratio of margin to highest utility, capped between 0.0 and 1.0
        confidence = 1.0
        if ranked_strategies[0].evaluation_metrics.utility_score != 0:
            confidence = min(1.0, max(0.1, abs(margin) / abs(ranked_strategies[0].evaluation_metrics.utility_score)))

        # 2. Compile advantages and disadvantages
        advantages = []
        disadvantages = []
        
        eval_m = selected.evaluation_metrics
        if eval_m.privacy_score >= 0.8:
            advantages.append("Fully offline execution preserves strict data privacy.")
        if eval_m.tool_utilization >= 0.5:
            advantages.append("Utilizes specialized tools for deterministic operations.")
        if eval_m.parallel_efficiency >= 0.7:
            advantages.append("High concurrency reduces overall execution latency.")
        if eval_m.cost == 0.0:
            advantages.append("Zero monetary cost (runs entirely on local resources).")
        else:
            disadvantages.append(f"Incurs cloud API usage cost of ${eval_m.cost:.4f}.")

        if eval_m.failure_probability >= 0.4:
            disadvantages.append(f"Elevated risk score of {eval_m.failure_probability:.2f} due to model constraints.")

        # 3. Formulate selection explanation
        selection_exp = (
            f"Strategy '{selected.name}' was selected because it achieved the highest "
            f"planning utility score of {selected.evaluation_metrics.utility_score} under the "
            f"current environment constraints."
        )

        # 4. Formulate rejected strategy explanations
        rejected_exps = {}
        for s in ranked_strategies[1:]:
            rejected_exps[s.name] = (
                f"Strategy '{s.name}' using policy '{s.policy.value}' was rejected "
                f"because its utility score ({s.evaluation_metrics.utility_score}) was lower "
                f"by a margin of {round(selected.evaluation_metrics.utility_score - s.evaluation_metrics.utility_score, 4)}."
            )

        return SelectionDecision(
            selected_strategy_name=selected.name,
            ranking_table=ranking_table,
            advantages=advantages,
            disadvantages=disadvantages,
            selection_explanation=selection_exp,
            rejected_explanations=rejected_exps,
            selection_margin=margin,
            selection_confidence=round(confidence, 4)
        )
