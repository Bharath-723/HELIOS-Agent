"""
HELIOS v2 - Knowledge, Memory & Retrieval Validation Suite
Validates memory hierarchy, indexing, caches, knowledge graphs, retrieval planners, and context assembly.
"""
import os
import sys
import time
import logging

sys.path.insert(0, os.path.abspath('.'))

from core.knowledge import (
    MemoryLayer,
    VerificationStatus,
    MemoryEntry,
    MemorySearchQuery,
    KnowledgeSource,
    RetrievalTask,
    RetrievalPlan,
    EvidenceBlock,
    RetrievalContext,
    MemoryLayersManager,
    MemorySearchEngine,
    KnowledgeManager,
    KnowledgeCache,
    KnowledgeStatisticsCompiler,
    RetrievalPlanner,
    ContextAssembler,
    RetrievalEngine
)
from core.reasoning import ReasoningContext, ReasoningEngine, ContextBuilder

# Setup logging to console
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("helios.knowledge.validation")

def run_knowledge_validation():
    log.info("Starting HELIOS v2 Knowledge & Memory Layer Validation...")
    
    # Instantiate components
    layers_mgr = MemoryLayersManager()
    kmgr = KnowledgeManager()
    engine = RetrievalEngine(layers_mgr, kmgr)
    stats_compiler = KnowledgeStatisticsCompiler()
    
    # ---------------------------------------------------------
    # Test 1: Memory Layers Addition and Indexing
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 1: Memory Layers Addition & Indexing (L1-L4)")
    
    # L1: Working Memory
    e1 = MemoryEntry("m1", MemoryLayer.L1_WORKING, "Current user is Bharat", tags=["user", "identity"], priority=5)
    layers_mgr.add_entry(e1)
    
    # L2: Session Memory
    e2 = MemoryEntry("m2", MemoryLayer.L2_SESSION, "Last query discussed Python versions", tags=["python", "session"], priority=3)
    layers_mgr.add_entry(e2)
    
    # L3: Persistent Memory
    e3 = MemoryEntry("m3", MemoryLayer.L3_PERSISTENT, "User prefers local offline processing", tags=["user", "preference"], priority=4)
    layers_mgr.add_entry(e3)
    
    # L4: Knowledge Memory
    e4 = MemoryEntry("m4", MemoryLayer.L4_KNOWLEDGE, "Python 3.12 was released in October 2023", tags=["python", "release"], priority=2)
    layers_mgr.add_entry(e4)
    
    assert len(layers_mgr.get_all_by_layer(MemoryLayer.L1_WORKING)) == 1
    assert len(layers_mgr.get_all_by_layer(MemoryLayer.L4_KNOWLEDGE)) == 1
    log.info("  ✓ Multi-layer storage verified successfully")

    # ---------------------------------------------------------
    # Test 2: Deterministic Memory Search Lookups
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 2: Memory Search Lookups (Keywords, Tags, Priorities)")
    search_eng = MemorySearchEngine(layers_mgr)
    
    # Query tag python, keywords Python, min priority 3
    q = MemorySearchQuery(keywords=["Python"], tags=["python"], min_priority=3)
    results = search_eng.search(q, [MemoryLayer.L1_WORKING, MemoryLayer.L2_SESSION, MemoryLayer.L3_PERSISTENT, MemoryLayer.L4_KNOWLEDGE])
    
    # Python 3.12 release info has priority 2 (below min_priority 3), so only L2 Python entry should match
    assert len(results) == 1, f"Expected 1 matching record, got {len(results)}"
    assert results[0][0].entry_id == "m2"
    log.info("  ✓ Query tagging and min_priority filter passed successfully")

    # ---------------------------------------------------------
    # Test 3: Knowledge Source Registry & Knowledge Graph
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 3: Knowledge Source Registry & Entity Knowledge Graph")
    
    # Register source
    source = kmgr.register_source(
        source_id="src_doc1",
        name="Python Release Docs",
        source_type="file",
        uri="file:///d:/docs/python312.txt",
        version="v1.0",
        reliability_score=0.9,
        verification_status=VerificationStatus.VERIFIED
    )
    assert kmgr.sources["src_doc1"].reliability_score == 0.9
    
    # Build graph
    kmgr.add_node("python_node", "language", {"name": "Python"})
    kmgr.add_node("release_312_node", "release", {"version": "3.12", "date": "2023-10-02"})
    kmgr.add_edge("python_node", "release_312_node", "has_version", {"verified": True}, "src_doc1")
    
    adj = kmgr.get_adjacent_nodes("python_node")
    assert len(adj) == 1
    assert adj[0][0].node_id == "release_312_node"
    assert adj[0][1] == "has_version"
    log.info("  ✓ Knowledge Source registration and Knowledge Graph connections passed")

    # ---------------------------------------------------------
    # Test 4: Reusable Cache & Statistics
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 4: Cache lookups, expiry, and Statistics compiles")
    cache = KnowledgeCache()
    
    # Store
    cache.store("test_q", [("entry", 1.0)], ttl_seconds=0.5)
    assert cache.get("test_q") is not None
    
    # Sleep to expire
    time.sleep(0.6)
    assert cache.get("test_q") is None
    log.info("  ✓ Cache TTL expiration passed")
    
    # Stats compiler
    stats = stats_compiler.compile_stats(layers_mgr, cache, [12.5, 8.0], [5, 2])
    assert stats.average_retrieval_latency_ms == 10.25
    assert stats.average_retrieval_depth == 3.5
    assert stats.memory_distribution["L1_WORKING"] == 1
    log.info("  ✓ Telemetry statistics compiled correctly: %s", stats)

    # ---------------------------------------------------------
    # Test 5: Retrieval Planning
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 5: Retrieval Planning from Reasoning ExecutionPlan")
    
    reasoning_eng = ReasoningEngine()
    cb_reason = ContextBuilder()
    rcontext = cb_reason.build(internet_available=True, local_model_available=True)
    
    # Generate execution plan
    exec_plan = reasoning_eng.plan("Search online for Python 3.12 release details.", rcontext)
    
    planner = RetrievalPlanner()
    ret_plan = planner.plan_retrieval(exec_plan)
    
    # Expected retrieval planner tasks to contain a web_search query targeting L4
    assert len(ret_plan.tasks) > 0
    assert any(rt.source_layer == MemoryLayer.L4_KNOWLEDGE for rt in ret_plan.tasks)
    log.info("  ✓ Retrieval tasks correctly planned. Estimated cost: $%.4f, latency: %.1fms", 
             ret_plan.cost_estimate, ret_plan.latency_estimate)

    # ---------------------------------------------------------
    # Test 6: Central Retrieval Pipeline Execution
    # ---------------------------------------------------------
    log.info("\n--------------------------------------------------")
    log.info("Test 6: Central Retrieval Pipeline (Planning -> Search -> Rank -> Assemble -> Validate)")
    
    # Add matching records to L4 knowledge with matching source metadata link
    layers_mgr.add_entry(MemoryEntry("m5", MemoryLayer.L4_KNOWLEDGE, "Python 3.12 release details online docs", {"source_id": "src_doc1"}, tags=["python"], priority=4))
    
    ret_ctx, ret_val, ret_trace = engine.execute_retrieval(exec_plan, [{"role": "user", "content": "hello"}])
    
    # Validate context and rankings
    assert len(ret_ctx.evidence_blocks) > 0
    # Top block should be Rank 1 and link to src_doc1
    top_block = ret_ctx.evidence_blocks[0]
    assert top_block.final_evidence_rank == 1
    assert top_block.source_id == "src_doc1"
    assert top_block.source_reliability == 0.9
    
    log.info("  ✓ Evidence collector and ranking correct (Rank 1: %s, Score: %.3f)", top_block.source_id, top_block.relevance_score)
    log.info("  ✓ Assembled context ID: %s, Evidence Blocks Count: %d", ret_ctx.context_id, len(ret_ctx.evidence_blocks))
    log.info("  ✓ Retrieval pipeline validation status: %s, Confidence: %.4f", ret_val.status, ret_val.retrieval_confidence)

    log.info("\n==================================================")
    log.info("HELIOS v2 Knowledge & Retrieval Layer Validation: SUCCESS")

if __name__ == '__main__':
    run_knowledge_validation()
