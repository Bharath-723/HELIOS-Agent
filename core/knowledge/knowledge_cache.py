"""
HELIOS v2 - Knowledge Cache
Caches query blocks, handles expiration intervals, and increments access counts.
"""
import time
from typing import Dict, Optional, Any
from core.knowledge.knowledge_models import CacheEntry
from core.knowledge.knowledge_logger import KnowledgeLogger

class KnowledgeCache:
    def __init__(self):
        # Maps query key to CacheEntry
        self._cache: Dict[str, CacheEntry] = {}
        self.logger = KnowledgeLogger()

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry:
            if time.time() > entry.expiry_timestamp:
                # Cache expired, remove it
                del self._cache[key]
                self.logger.log_event("cache_expired", {"cache_key": key})
                return None
                
            # Increment access stats (we create a new frozen entry to simulate updates)
            updated = CacheEntry(
                key=entry.key,
                data=entry.data,
                expiry_timestamp=entry.expiry_timestamp,
                access_count=entry.access_count + 1,
                cache_hits=entry.cache_hits + 1
            )
            self._cache[key] = updated
            self.logger.log_cache_hit(key, updated.access_count)
            return updated.data
        return None

    def store(self, key: str, data: Any, ttl_seconds: float):
        expiry = time.time() + ttl_seconds
        entry = CacheEntry(
            key=key,
            data=data,
            expiry_timestamp=expiry,
            access_count=1,
            cache_hits=0
        )
        self._cache[key] = entry
        self.logger.log_event("cache_store", {"cache_key": key, "ttl": ttl_seconds})

    def clear(self):
        self._cache.clear()
        self.logger.log_event("cache_clear", {})
