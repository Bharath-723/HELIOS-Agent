"""
HELIOS v2 - Knowledge Statistics Compiler
Aggregates subsystem usage details: memory sizes, latency averages, and cache metrics.
"""
from typing import List, Dict
from core.knowledge.knowledge_models import KnowledgeStats, MemoryLayer
from core.knowledge.memory_layers import MemoryLayersManager
from core.knowledge.knowledge_cache import KnowledgeCache

class KnowledgeStatisticsCompiler:
    def compile_stats(
        self,
        layers_mgr: MemoryLayersManager,
        cache: KnowledgeCache,
        retrieval_latencies: List[float],
        retrieval_depths: List[int]
    ) -> KnowledgeStats:
        
        # 1. Cache hit ratio
        total_accesses = 0
        total_hits = 0
        for entry in cache._cache.values():
            total_accesses += entry.access_count
            total_hits += entry.cache_hits
            
        hit_ratio = 0.0
        if total_accesses > 0:
            hit_ratio = total_hits / total_accesses

        # 2. Average latency
        avg_latency = 0.0
        if retrieval_latencies:
            avg_latency = sum(retrieval_latencies) / len(retrieval_latencies)

        # 3. Average depth
        avg_depth = 0.0
        if retrieval_depths:
            avg_depth = sum(retrieval_depths) / len(retrieval_depths)

        # 4. Memory distribution
        dist = {
            "L1_WORKING": len(layers_mgr.get_all_by_layer(MemoryLayer.L1_WORKING)),
            "L2_SESSION": len(layers_mgr.get_all_by_layer(MemoryLayer.L2_SESSION)),
            "L3_PERSISTENT": len(layers_mgr.get_all_by_layer(MemoryLayer.L3_PERSISTENT)),
            "L4_KNOWLEDGE": len(layers_mgr.get_all_by_layer(MemoryLayer.L4_KNOWLEDGE))
        }

        # Projected memory utilization in bytes (mock weight: 100 bytes per memory record)
        utilization = len(layers_mgr.entries) * 100

        # Knowledge coverage (mock ratio of verified vs suspicious registries)
        coverage = 1.0

        return KnowledgeStats(
            hit_ratio=round(hit_ratio, 4),
            average_retrieval_latency_ms=round(avg_latency, 2),
            memory_utilization_bytes=utilization,
            knowledge_coverage=coverage,
            average_retrieval_depth=round(avg_depth, 2),
            memory_distribution=dist
        )
