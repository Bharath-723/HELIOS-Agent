"""
HELIOS v2 - Planning Memory Cache
Stores, indexes, and retrieves successful plan structures using a fingerprint-based cache to enable context and structure reuse.
"""
import logging
from typing import Dict, Optional
from core.reasoning.reasoning_models import TaskIntent, ReasoningContext, ExecutionGraph

log = logging.getLogger("helios.reasoning.memory")

class PlanningMemory:
    def __init__(self):
        # Maps semantic key to ExecutionGraph
        self._cache: Dict[str, ExecutionGraph] = {}

    def _generate_key(self, intent: TaskIntent, context: ReasoningContext) -> str:
        # Create a stable semantic key from intent attributes and context parameters
        tools_str = ",".join(sorted(intent.requires_tools))
        return (
            f"{intent.category.value}:{intent.privacy_requirement}:{intent.requires_internet}:"
            f"{tools_str}:{context.internet_available}:{context.local_model_available}"
        )

    def get(self, intent: TaskIntent, context: ReasoningContext) -> Optional[ExecutionGraph]:
        key = self._generate_key(intent, context)
        graph = self._cache.get(key)
        if graph:
            log.info("Planning Memory HIT for key='%s'", key)
            return graph
        log.info("Planning Memory MISS for key='%s'", key)
        return None

    def store(self, intent: TaskIntent, context: ReasoningContext, graph: ExecutionGraph):
        key = self._generate_key(intent, context)
        self._cache[key] = graph
        log.info("Stored plan graph in Planning Memory under key='%s'", key)

    def clear(self):
        self._cache.clear()
