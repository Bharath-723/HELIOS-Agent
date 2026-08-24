"""
HELIOS v2 - Hierarchical Memory Storage Layers
Manages L1 (Working), L2 (Session), L3 (Persistent), and L4 (Knowledge) storage layers.
"""
from typing import Dict, List, Optional
from core.knowledge.knowledge_models import MemoryEntry, MemoryLayer
from core.knowledge.memory_index import MemoryIndex
from core.knowledge.knowledge_logger import KnowledgeLogger

class MemoryLayersManager:
    def __init__(self):
        # Maps entry_id -> MemoryEntry
        self.entries: Dict[str, MemoryEntry] = {}
        
        # Inverted index for fast deterministic retrieval scans
        self.index = MemoryIndex()
        self.logger = KnowledgeLogger()

    def add_entry(self, entry: MemoryEntry):
        self.entries[entry.entry_id] = entry
        self.index.add_entry(entry)
        self.logger.log_event("memory_add", {
            "entry_id": entry.entry_id,
            "layer": entry.layer.name,
            "tags": entry.tags
        })

    def delete_entry(self, entry_id: str) -> bool:
        entry = self.entries.get(entry_id)
        if entry:
            self.index.remove_entry(entry_id, entry.tags, entry.metadata)
            del self.entries[entry_id]
            self.logger.log_event("memory_delete", {"entry_id": entry_id})
            return True
        return False

    def get_entry(self, entry_id: str) -> Optional[MemoryEntry]:
        return self.entries.get(entry_id)

    def get_all_by_layer(self, layer: MemoryLayer) -> List[MemoryEntry]:
        return [t for t in self.entries.values() if t.layer == layer]

    def clear_layer(self, layer: MemoryLayer):
        ids_to_del = [tid for tid, t in self.entries.items() if t.layer == layer]
        for tid in ids_to_del:
            self.delete_entry(tid)
        self.logger.log_event("memory_clear_layer", {"layer": layer.name})
