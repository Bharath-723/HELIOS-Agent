"""
HELIOS v2 - Memory Search Heuristics
Implements deterministic, backend-agnostic metadata, tag, keyword, time, and priority-based scans.
"""
from typing import List, Tuple
from core.knowledge.knowledge_models import MemoryEntry, MemorySearchQuery, MemoryLayer
from core.knowledge.memory_layers import MemoryLayersManager

class MemorySearchEngine:
    def __init__(self, layers_manager: MemoryLayersManager):
        self.mgr = layers_manager

    def search(self, query: MemorySearchQuery, layers: List[MemoryLayer]) -> List[Tuple[MemoryEntry, float]]:
        """
        Executes query filters across selected memory layers.
        Returns entries paired with computed relevance score, sorted descending.
        """
        # Collect candidate entries from requested layers
        candidates: List[MemoryEntry] = []
        for layer in layers:
            candidates.extend(self.mgr.get_all_by_layer(layer))

        results: List[Tuple[MemoryEntry, float]] = []

        for entry in candidates:
            # 1. Min Priority Filter
            if entry.priority < query.min_priority:
                continue

            # 2. Timestamp Filter
            if query.start_time is not None and entry.timestamp < query.start_time:
                continue
            if query.end_time is not None and entry.timestamp > query.end_time:
                continue

            # 3. Tag Filter (Matches if tags are empty, or if there is at least one overlap)
            if query.tags:
                entry_tags_norm = {t.lower().strip() for t in entry.tags}
                query_tags_norm = {t.lower().strip() for t in query.tags}
                if not entry_tags_norm.intersection(query_tags_norm):
                    continue

            # 4. Metadata Filtering
            metadata_match = True
            for k, v in query.metadata_filter.items():
                if k not in entry.metadata or str(entry.metadata[k]) != str(v):
                    metadata_match = False
                    break
            if not metadata_match:
                continue

            # 5. Keyword Matching Score
            relevance = 1.0
            if query.keywords:
                matched_count = 0
                content_lower = entry.content.lower()
                for kw in query.keywords:
                    if kw.lower().strip() in content_lower:
                        matched_count += 1
                if matched_count == 0:
                    # If keyword search was specified but we got zero matches, reject
                    continue
                relevance = matched_count / len(query.keywords)

            # 6. Apply Priority Bonus
            # Higher priority records get a minor boost to float up (0.05 per level)
            score = relevance + (entry.priority * 0.05)
            results.append((entry, round(score, 4)))

        # Sort descending by score, then priority, then timestamp
        results.sort(key=lambda x: (-x[1], -x[0].priority, -x[0].timestamp))
        return results
