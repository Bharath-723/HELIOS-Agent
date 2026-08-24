"""
HELIOS v2 - Plan Refiner
Coordinative refiner applying dependency, parallel, and resource optimizers with Plan Equivalence Verification.
"""
import logging
from typing import List, Dict, Tuple
from core.reasoning.reasoning_models import AtomicTask, ExecutionGraph
from core.reasoning.dependency_optimizer import DependencyOptimizer
from core.reasoning.parallel_optimizer import ParallelOptimizer
from core.reasoning.resource_optimizer import ResourceOptimizer
from core.reasoning.execution_graph_builder import ExecutionGraphBuilder

log = logging.getLogger("helios.reasoning.refiner")

class PlanRefiner:
    def __init__(self):
        self.dep_opt = DependencyOptimizer()
        self.par_opt = ParallelOptimizer()
        self.res_opt = ResourceOptimizer()
        self.graph_builder = ExecutionGraphBuilder()

    def verify_equivalence(self, original_tasks: List[AtomicTask], refined_tasks: List[AtomicTask]) -> Tuple[bool, str]:
        """
        Semantic Plan Equivalence Verification.
        Ensures refined plan produces equivalent inputs/outputs and does not lose required operations.
        """
        orig_map = {t.task_id: t for t in original_tasks}
        ref_map = {t.task_id: t for t in refined_tasks}

        # Check 1: We did not drop any vital output target
        for tid, t in orig_map.items():
            if tid not in ref_map and "connectivity" not in t.description.lower():
                # Pruning connectivity check is allowed, but dropping main note/search/file tasks is a violation!
                return False, f"Semantic mismatch: Vital task '{tid}' ({t.description}) was dropped."

        # Check 2: Preconditions/postconditions/expected outputs are maintained
        for tid, t in ref_map.items():
            if tid in orig_map:
                orig_t = orig_map[tid]
                if t.expected_output != orig_t.expected_output:
                    return False, f"Expected output changed for task '{tid}': {t.expected_output} vs {orig_t.expected_output}"

        # Check 3: Check DAG cycle properties
        try:
            self.graph_builder.build_graph(refined_tasks)
        except ValueError as val_err:
            return False, f"Refinement introduced invalid DAG dependencies: {val_err}"

        return True, "Plans are semantically equivalent."

    def refine(self, graph: ExecutionGraph) -> Tuple[ExecutionGraph, str]:
        tasks = list(graph.tasks.values())
        
        # 1. Apply optimizations sequentially
        tasks_dep = self.dep_opt.optimize(tasks)
        tasks_par = self.par_opt.optimize(tasks_dep)
        tasks_res = self.res_opt.optimize(tasks_par)
        
        # 2. Verify equivalence
        is_equivalent, reason = self.verify_equivalence(tasks, tasks_res)
        if not is_equivalent:
            log.warning("Refinement rejected: %s. Returning original plan.", reason)
            return graph, f"Refinement failed equivalence: {reason}"

        # 3. Compile new graph
        refined_graph = self.graph_builder.build_graph(tasks_res)
        return refined_graph, "Successfully optimized dependencies, parallel levels, and model selection."
