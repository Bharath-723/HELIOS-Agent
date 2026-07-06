import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from core.routing.routing_models import RoutingResult, DecisionSnapshot

log = logging.getLogger("helios.routing.diagnostics")

class RoutingDiagnostics:
    def __init__(self, output_dir: str = "data/diagnostics"):
        self.output_dir = Path(__file__).parent.parent.parent / output_dir
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            log.error("Failed to create diagnostics output folder: %s", exc)

    def compile_snapshot(self, result: RoutingResult, timings: Dict[str, float]) -> DecisionSnapshot:
        from core.routing.candidate_manager import CandidateManager
        from core.routing.score_engine import ScoreEngine
        
        mgr = CandidateManager()
        engine_scores = ScoreEngine()
        capabilities_profiles = mgr.profiles
        
        effective_caps = {}
        for model in result.candidate_ranking:
            effective_caps[model] = engine_scores.get_effective_capability(model, result.context)
            
        snapshot = DecisionSnapshot(
            prompt=result.context.prompt,
            extracted_requirements={
                "privacy": result.features.privacy_score,
                "freshness": result.features.freshness_score,
                "complexity": result.features.complexity_score
            },
            candidate_models=result.candidate_ranking,
            capability_profiles={m: capabilities_profiles.get(m, {}) for m in result.candidate_ranking},
            effective_capabilities=effective_caps,
            utility_scores=result.decision_trace.score_breakdown.get("all_candidates_utilities", {}) if result.decision_trace else {},
            capability_mismatches=result.capability_mismatches,
            ranking=result.candidate_ranking,
            selected_model=result.selected_model,
            rejected_models=[m for m in result.candidate_ranking if m != result.selected_model],
            selection_margin=result.selection_margin,
            confidence=result.explanation.confidence,
            triggered_constraints=result.constraints_triggered,
            execution_time_ms=timings.get("total_time_ms", result.execution_time_ms),
            timestamp=datetime.now().isoformat(),
            algorithm_version=result.algorithm_version,
            strategy_version=result.strategy_name
        )
        return snapshot

    def export_snapshot_json(self, snapshot: DecisionSnapshot, file_prefix: str = "decision_snapshot"):
        snapshot_dict = {
            "prompt": snapshot.prompt,
            "extracted_requirements": snapshot.extracted_requirements,
            "candidate_models": snapshot.candidate_models,
            "utility_scores": snapshot.utility_scores,
            "capability_mismatches": snapshot.capability_mismatches,
            "ranking": snapshot.ranking,
            "selected_model": snapshot.selected_model,
            "rejected_models": snapshot.rejected_models,
            "selection_margin": snapshot.selection_margin,
            "confidence": snapshot.confidence,
            "triggered_constraints": snapshot.triggered_constraints,
            "execution_time_ms": snapshot.execution_time_ms,
            "timestamp": snapshot.timestamp,
            "algorithm_version": snapshot.algorithm_version,
            "strategy_version": snapshot.strategy_version
        }
        
        snapshot_path = self.output_dir / f"{file_prefix}.json"
        try:
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(snapshot_dict, f, indent=2)
            log.info("Successfully exported decision snapshot JSON to %s", snapshot_path)
        except Exception as exc:
            log.error("Failed to export decision snapshot JSON: %s", exc)
            
    def export_ranking_json(self, ranking: List[str], file_prefix: str = "candidate_ranking"):
        ranking_path = self.output_dir / f"{file_prefix}.json"
        try:
            with open(ranking_path, "w", encoding="utf-8") as f:
                json.dump({"candidate_ranking": ranking}, f, indent=2)
            log.info("Successfully exported candidate ranking JSON to %s", ranking_path)
        except Exception as exc:
            log.error("Failed to export candidate ranking JSON: %s", exc)
            
    def export_summary_json(self, stats: Dict[str, Any], file_prefix: str = "routing_summary"):
        summary_path = self.output_dir / f"{file_prefix}.json"
        try:
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)
            log.info("Successfully exported routing summary JSON to %s", summary_path)
        except Exception as exc:
            log.error("Failed to export routing summary JSON: %s", exc)
