"""
HELIOS v2 - Planning Trace Recorder
Compiles stage-preserving planning trace logs for the adaptive engine.
"""
from typing import Dict, Any, List
from core.reasoning.reasoning_models import PlanningTrace, PlanningStrategy

class PlanningTraceRecorder:
    def __init__(self):
        self.stages: Dict[str, Any] = {}

    def record_stage(self, stage_name: str, input_summary: Any, output_summary: Any):
        """Records details of a specific planning stage to preserve timeline logs."""
        self.stages[stage_name] = {
            "input": input_summary,
            "output": output_summary
        }

    def compile(
        self,
        all_strategies: List[PlanningStrategy],
        filtered_strategies: List[PlanningStrategy],
        ranked_strategies: List[PlanningStrategy],
        selected_name: str,
        duration_ms: float
    ) -> PlanningTrace:
        all_names = [s.name for s in all_strategies]
        filtered_names = [s.name for s in filtered_strategies]
        
        ranked_info = []
        for s in ranked_strategies:
            ranked_info.append({
                "name": s.name,
                "utility": s.evaluation_metrics.utility_score
            })

        rationale = (
            f"Evaluated {len(all_names)} policies. Filtered to {len(filtered_names)} valid candidates. "
            f"Selected '{selected_name}' with highest utility. Process took {duration_ms:.2f}ms."
        )

        return PlanningTrace(
            stages=self.stages.copy(),
            all_strategies=all_names,
            filtered_strategies=filtered_names,
            ranked_strategies=ranked_info,
            selected_strategy_name=selected_name,
            decision_rationale=rationale,
            planning_duration_ms=duration_ms
        )
