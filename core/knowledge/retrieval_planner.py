"""
HELIOS v2 - Retrieval Planner
Analyzes ExecutionPlans to determine retrieval tasks, priorities, estimated latencies, and costs.
"""
import uuid
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.reasoning.reasoning_models import ExecutionPlan
from core.knowledge.knowledge_models import RetrievalPlan, RetrievalTask, MemoryLayer

class RetrievalPlanner:
    def __init__(self, rules_path: Optional[str if 'Optional' in globals() else str] = None):
        if rules_path is None:
            rules_path = str(Path(__file__).parent / "knowledge_rules.json")
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def plan_retrieval(self, plan: ExecutionPlan) -> RetrievalPlan:
        tasks: List[RetrievalTask] = []
        cost_est = 0.0
        lat_est = 0.0
        
        cost_latency_settings = self.rules.get(
            "retrieval_cost_latency",
            {
                "working_memory": { "latency_ms": 5.0, "cost": 0.0 },
                "session_memory": { "latency_ms": 15.0, "cost": 0.0 },
                "persistent_memory": { "latency_ms": 50.0, "cost": 0.0 },
                "knowledge_memory": { "latency_ms": 120.0, "cost": 0.001 },
                "web_search": { "latency_ms": 1500.0, "cost": 0.005 }
            }
        )

        # Iterate over plan graph tasks to identify information requirements
        for t in plan.graph.tasks.values():
            # If the task requires search, we need external search and knowledge memory
            if t.required_tool == "WebSearch":
                settings = cost_latency_settings.get("web_search", {"latency_ms": 1500.0, "cost": 0.005})
                rt = RetrievalTask(
                    task_id=f"retrieval-{uuid.uuid4().hex[:6]}",
                    source_layer=MemoryLayer.L4_KNOWLEDGE,
                    query=t.description,
                    priority=t.priority,
                    estimated_latency_ms=settings["latency_ms"],
                    estimated_cost=settings["cost"]
                )
                tasks.append(rt)
                cost_est += rt.estimated_cost
                lat_est = max(lat_est, rt.estimated_latency_ms)  # Concurrency simulation
                
            elif t.required_tool == "NotesManager":
                # Notes manager accesses L3 persistent memory
                settings = cost_latency_settings.get("persistent_memory", {"latency_ms": 50.0, "cost": 0.0})
                rt = RetrievalTask(
                    task_id=f"retrieval-{uuid.uuid4().hex[:6]}",
                    source_layer=MemoryLayer.L3_PERSISTENT,
                    query=t.description,
                    priority=t.priority,
                    estimated_latency_ms=settings["latency_ms"],
                    estimated_cost=settings["cost"]
                )
                tasks.append(rt)
                cost_est += rt.estimated_cost
                lat_est += rt.estimated_latency_ms
                
            else:
                # Default checks use L1/L2
                settings = cost_latency_settings.get("working_memory", {"latency_ms": 5.0, "cost": 0.0})
                rt = RetrievalTask(
                    task_id=f"retrieval-{uuid.uuid4().hex[:6]}",
                    source_layer=MemoryLayer.L1_WORKING,
                    query=t.description,
                    priority=1,
                    estimated_latency_ms=settings["latency_ms"],
                    estimated_cost=settings["cost"]
                )
                tasks.append(rt)
                cost_est += rt.estimated_cost
                lat_est += rt.estimated_latency_ms

        return RetrievalPlan(
            original_plan_id=plan.plan_id,
            tasks=tasks,
            cost_estimate=round(cost_est, 4),
            latency_estimate=round(lat_est, 2)
        )
