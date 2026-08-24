"""
HELIOS v2 - Memory Index
Maintains inverted tag indexes and metadata attribute maps for fast entry lookups.
"""
from typing import Dict, Set, List
from core.knowledge.knowledge_models import MemoryEntry

class MemoryIndex:
    def __init__(self):
        # Maps tag -> set of entry_ids
        self.tag_index: Dict[str, Set[str]] = {}
        # Maps metadata key -> value -> set of entry_ids
        self.metadata_index: Dict[str, Dict[Any if 'Any' in globals() else str, Set[str]]] = {}

    def add_entry(self, entry: MemoryEntry):
        # Index tags
        for tag in entry.tags:
            tag_norm = tag.lower().strip()
            if tag_norm not in self.tag_index:
                self.tag_index[tag_norm] = set()
            self.tag_index[tag_norm].add(entry.entry_id)

        # Index metadata attributes
        for k, v in entry.metadata.items():
            if k not in self.metadata_index:
                self.metadata_index[k] = {}
            # Standardize v to string representation for safe dict hashing
            v_hashable = str(v)
            if v_hashable not in self.metadata_index[k]:
                self.metadata_index[k][v_hashable] = set()
            self.metadata_index[k][v_hashable].add(entry.entry_id)

    def remove_entry(self, entry_id: str, tags: List[str], metadata: Dict[str, Any if 'Any' in globals() else str]):
        for tag in tags:
            tag_norm = tag.lower().strip()
            if tag_norm in self.tag_index:
                self.tag_index[tag_norm].discard(entry_id)

        for k, v in metadata.items():
            v_hashable = str(v)
            if k in self.metadata_index and v_hashable in self.metadata_index[k]:
                self.metadata_index[k][v_hashable].discard(entry_id)

    def get_by_tag(self, tag: str) -> Set[str]:
        return self.tag_index.get(tag.lower().strip(), set())

    def get_by_metadata(self, key: str, value: Any if 'Any' in globals() else str) -> Set[str]:
        v_hashable = str(value)
        return self.metadata_index.get(key, {}).get(v_hashable, set())
