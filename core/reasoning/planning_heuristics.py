"""
HELIOS v2 - Planning Heuristics Engine
Loads and computes scoring factors for task locality, tool utilization, concurrency, and costs.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.reasoning.reasoning_models import AtomicTask

log = logging.getLogger("helios.reasoning.heuristics")

class PlanningHeuristicsEngine:
    def __init__(self, heuristics_path: Optional[str] = None):
        if heuristics_path is None:
            heuristics_path = str(Path(__file__).parent / "planning_heuristics.json")
        self.heuristics = self._load_heuristics(heuristics_path)

    def _load_heuristics(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            log.error("Failed to load planning heuristics: %s", exc)
            return {}

    def get_value(self, key: str, default: Any = None) -> Any:
        return self.heuristics.get(key, default)

    def evaluate_locality(self, tasks: List[AtomicTask]) -> float:
        """Score from 0.0 (all cloud) to 1.0 (all local)."""
        if not tasks:
            return 1.0
        local_count = sum(1 for t in tasks if t.required_model in ("gemma3", "mistral"))
        return local_count / len(tasks)

    def evaluate_tool_utilization(self, tasks: List[AtomicTask]) -> float:
        """Score from 0.0 (no tools) to 1.0 (all tasks use tools)."""
        if not tasks:
            return 0.0
        tool_count = sum(1 for t in tasks if t.required_tool is not None)
        return tool_count / len(tasks)

    def evaluate_parallel_efficiency(self, tasks: List[AtomicTask], parallel_groups: List[List[str]]) -> float:
        """Score based on target concurrency metrics in config."""
        if not parallel_groups:
            return 0.0
        
        targets = self.get_value("concurrency_targets", {})
        opt_tasks = targets.get("optimal_tasks_per_level", 2)
        
        total_score = 0.0
        for group in parallel_groups:
            size = len(group)
            if size > 1:
                # Highly efficient concurrent execution
                efficiency = min(1.0, size / opt_tasks)
                total_score += efficiency
            else:
                total_score += 0.2 # Sequential penalty
                
        return total_score / len(parallel_groups)
