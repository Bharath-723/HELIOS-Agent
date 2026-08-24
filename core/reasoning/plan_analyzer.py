"""
HELIOS v2 - Plan Analyzer
Inspects ExecutionGraph structures to identify bottlenecks, duplicate operations, and optimization opportunities.
"""
from typing import List, Dict, Set
from core.reasoning.reasoning_models import ExecutionGraph, AtomicTask

class PlanAnalyzer:
    def analyze(self, graph: ExecutionGraph) -> Dict[str, List[str]]:
        findings = {
            "redundant_tasks": [],
            "unnecessary_dependencies": [],
            "duplicate_operations": [],
            "tool_switch_overhead": [],
            "parallel_opportunities": []
        }

        tasks = list(graph.tasks.values())
        task_ids = list(graph.tasks.keys())

        # 1. Detect redundant tasks (e.g. multiple connectivity checks)
        conn_checks = [t.task_id for t in tasks if t.required_tool == "DesktopAgent" and "connectivity" in t.description.lower()]
        if len(conn_checks) > 1:
            # All but the first connectivity check are redundant
            findings["redundant_tasks"].extend(conn_checks[1:])

        # 2. Detect duplicate operations (e.g. multiple tasks performing the exact same action)
        seen_descriptions = {}
        for t in tasks:
            desc_norm = t.description.lower().strip()
            if desc_norm in seen_descriptions:
                findings["duplicate_operations"].append(t.task_id)
            else:
                seen_descriptions[desc_norm] = t.task_id

        # 3. Detect unnecessary dependencies (transitives)
        for t in tasks:
            for dep in t.dependencies:
                # If dep is also a transitive dependency of another dependency of t, it is redundant
                other_deps = [d for d in t.dependencies if d != dep]
                for od in other_deps:
                    if od in graph.tasks:
                        # Simple check: does od depend on dep?
                        if dep in graph.tasks[od].dependencies:
                            findings["unnecessary_dependencies"].append(f"{t.task_id}->{dep}")

        # 4. Tool switching overhead (sequential tasks switching tools back and forth)
        for i in range(len(graph.execution_order) - 1):
            t1 = graph.tasks[graph.execution_order[i]]
            t2 = graph.tasks[graph.execution_order[i+1]]
            if t1.required_tool and t2.required_tool and t1.required_tool != t2.required_tool:
                findings["tool_switch_overhead"].append(f"{t1.task_id}->{t2.task_id}")

        # 5. Parallel opportunities (non-dependent sequential levels containing single tasks)
        single_task_levels = [g for g in graph.parallel_groups if len(g) == 1]
        if len(single_task_levels) > 2:
            findings["parallel_opportunities"].append("Opportunity to merge non-dependent sequence levels to maximize concurrency.")

        return findings
