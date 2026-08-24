"""
HELIOS v2 - Retrieval Trace Recorder
Compiles stage-preserving traces of the retrieval pipeline.
"""
from typing import Dict, List, Any
from core.knowledge.knowledge_models import RetrievalTrace

class RetrievalTraceRecorder:
    def __init__(self):
        self.stages: Dict[str, Any] = {}
        self.search_decisions: List[str] = []
        self.timings_ms: Dict[str, float] = {}
        self.cache_hits: List[str] = []

    def record_stage(self, stage_name: str, input_summary: Any, output_summary: Any):
        self.stages[stage_name] = {
            "input": input_summary,
            "output": output_summary
        }

    def add_decision(self, decision: str):
        self.search_decisions.append(decision)

    def record_timing(self, stage: str, duration_ms: float):
        self.timings_ms[stage] = duration_ms

    def record_cache_hit(self, key: str):
        self.cache_hits.append(key)

    def compile(self) -> RetrievalTrace:
        return RetrievalTrace(
            stages=self.stages.copy(),
            search_decisions=self.search_decisions.copy(),
            timings_ms=self.timings_ms.copy(),
            cache_hits=self.cache_hits.copy()
        )
