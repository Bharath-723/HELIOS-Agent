"""
HELIOS v2 - Execution Graph Builder
Decoupled builder class for DAG construction, dependency sorting, and verification checks.
"""
from typing import List, Dict, Set
from core.reasoning.reasoning_models import AtomicTask, ExecutionGraph

class ExecutionGraphBuilder:
    def build_graph(self, tasks: List[AtomicTask]) -> ExecutionGraph:
        task_dict = {t.task_id: t for t in tasks}
        
        # 1. Dependency adjacency mapping
        adj: Dict[str, List[str]] = {t.task_id: [] for t in tasks}
        in_degree: Dict[str, int] = {t.task_id: 0 for t in tasks}
        
        for t in tasks:
            for dep in t.dependencies:
                if dep in adj:
                    adj[dep].append(t.task_id)
                    in_degree[t.task_id] += 1

        # 2. Topological Sort (Kahn's Algorithm)
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        order = []
        
        while queue:
            queue.sort() # Ensure deterministic topological ordering
            curr = queue.pop(0)
            order.append(curr)
            
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(tasks):
            raise ValueError("Circular dependency detected in reasoning subtasks!")

        # 3. Parallel levels grouping
        levels: Dict[str, int] = {t.task_id: 0 for t in tasks}
        for tid in order:
            t = task_dict[tid]
            max_dep_level = -1
            for dep in t.dependencies:
                if dep in levels:
                    max_dep_level = max(max_dep_level, levels[dep])
            levels[tid] = max_dep_level + 1

        max_level = max(levels.values()) if levels else -1
        parallel_groups = []
        for l in range(max_level + 1):
            group = [tid for tid, lvl in levels.items() if lvl == l]
            group.sort()
            parallel_groups.append(group)

        # 4. Fallback nodes, retry policies, and verification checks
        fallbacks = {}
        retries = {}
        verifications = []
        
        for t in tasks:
            fallbacks[t.task_id] = f"{t.task_id}_fallback"
            retries[t.task_id] = t.retry_limit
            if t.verification_required:
                verifications.append(f"verify_output_schema_{t.task_id}")
                
        verifications.append("assert_no_syntactic_errors")
        verifications.append("assert_correct_json_format")

        return ExecutionGraph(
            tasks=task_dict,
            execution_order=order,
            parallel_groups=parallel_groups,
            fallback_nodes=fallbacks,
            retry_policies=retries,
            verification_checks=verifications
        )
