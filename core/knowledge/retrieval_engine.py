"""
HELIOS v2 - Retrieval Engine
Coordinates retrieval planning, memory/knowledge search, evidence collection, ranking, assembly, and validation.
"""
import time
import logging
from typing import List, Dict, Any, Tuple
from core.reasoning.reasoning_models import ExecutionPlan
from core.knowledge.knowledge_models import (
    RetrievalPlan,
    RetrievalContext,
    EvidenceBlock,
    RetrievalValidationResult,
    MemorySearchQuery,
    MemoryLayer,
    RetrievalTrace
)
from core.knowledge.retrieval_planner import RetrievalPlanner
from core.knowledge.memory_layers import MemoryLayersManager
from core.knowledge.memory_search import MemorySearchEngine
from core.knowledge.knowledge_manager import KnowledgeManager
from core.knowledge.knowledge_cache import KnowledgeCache
from core.knowledge.context_assembler import ContextAssembler
from core.knowledge.retrieval_trace import RetrievalTraceRecorder

log = logging.getLogger("helios.knowledge.retrieval")

class RetrievalEngine:
    def __init__(self, layers_manager: MemoryLayersManager, knowledge_manager: KnowledgeManager):
        self.layers_mgr = layers_manager
        self.knowledge_mgr = knowledge_manager
        
        self.planner = RetrievalPlanner()
        self.search_engine = MemorySearchEngine(layers_manager)
        self.cache = KnowledgeCache()
        self.assembler = ContextAssembler()

        # Telemetry metrics
        self.retrieval_latencies: List[float] = []
        self.retrieval_depths: List[int] = []

    def execute_retrieval(
        self, plan: ExecutionPlan, conversation_history: List[Dict[str, str]]
    ) -> Tuple[RetrievalContext, RetrievalValidationResult, RetrievalTrace]:
        t0 = time.perf_counter()
        trace_recorder = RetrievalTraceRecorder()

        # Stage 1: Retrieval Planning
        retrieval_plan = self.planner.plan_retrieval(plan)
        trace_recorder.record_stage(
            "retrieval_planning",
            input_summary={"original_plan_id": plan.plan_id},
            output_summary={"tasks_count": len(retrieval_plan.tasks)}
        )

        # Stage 2 & 3: Memory Search & Knowledge Search
        raw_evidence_candidates: List[Tuple[Any, float]] = []
        
        for task in retrieval_plan.tasks:
            # Check Cache first
            cached_data = self.cache.get(task.query)
            if cached_data is not None:
                trace_recorder.record_cache_hit(task.query)
                raw_evidence_candidates.extend(cached_data)
                continue

            # Build query
            q = MemorySearchQuery(
                keywords=task.query.split(),
                min_priority=task.priority
            )
            
            # Execute Memory Search / Knowledge Search
            layer_results = self.search_engine.search(q, [task.source_layer])
            
            # Cache the result block (expiry standard: 60s)
            self.cache.store(task.query, layer_results, 60.0)
            raw_evidence_candidates.extend(layer_results)

        trace_recorder.record_stage(
            "search_and_lookup",
            input_summary={"queries_count": len(retrieval_plan.tasks)},
            output_summary={"total_raw_found": len(raw_evidence_candidates)}
        )

        # Stage 4: Evidence Collection
        evidence_blocks: List[EvidenceBlock] = []
        for entry, score in raw_evidence_candidates:
            # Source lookup reliability defaults to 1.0 if not external
            reliability = 1.0
            source_id = entry.metadata.get("source_id", "local_memory")
            source = self.knowledge_mgr.sources.get(source_id)
            if source:
                reliability = source.reliability_score
                
            block = EvidenceBlock(
                source_id=source_id,
                content=entry.content,
                metadata=entry.metadata.copy(),
                relevance_score=score,
                source_reliability=reliability,
                timestamp=entry.timestamp
            )
            evidence_blocks.append(block)

        # Stage 5: Evidence Ranking
        # Ranks by Relevance Score (80% weight) + Source Reliability (20% weight)
        def compute_rank_score(eb: EvidenceBlock) -> float:
            return (eb.relevance_score * 0.8) + (eb.source_reliability * 0.2)
            
        ranked_blocks = sorted(evidence_blocks, key=compute_rank_score, reverse=True)
        
        # Assign final rank indicators
        final_ranked_blocks = []
        for rank_idx, block in enumerate(ranked_blocks):
            final_ranked_blocks.append(
                EvidenceBlock(
                    source_id=block.source_id,
                    content=block.content,
                    metadata=block.metadata,
                    relevance_score=block.relevance_score,
                    source_reliability=block.source_reliability,
                    timestamp=block.timestamp,
                    final_evidence_rank=rank_idx + 1
                )
            )

        trace_recorder.record_stage(
            "evidence_ranking",
            input_summary={"unsorted_count": len(evidence_blocks)},
            output_summary={"ranked_order": [f"Rank {eb.final_evidence_rank}: {eb.source_id}" for eb in final_ranked_blocks]}
        )

        # Stage 6: Context Assembly
        # Group active constraints from the plan
        constraints = plan.intent.requires_tools.copy()
        if plan.intent.requires_internet:
            constraints.append("requires_internet")
            
        retrieval_context = self.assembler.assemble_context(
            conversation_history=conversation_history,
            evidence_blocks=final_ranked_blocks,
            active_constraints=constraints
        )

        trace_recorder.record_stage(
            "context_assembly",
            input_summary={"evidence_count": len(final_ranked_blocks)},
            output_summary={"context_id": retrieval_context.context_id}
        )

        # Stage 7: Retrieval Validation
        validation_errors = []
        validation_warnings = []
        
        # Validation checks: If plan required internet and no online sources are retrieved, issue warning
        if plan.intent.requires_internet and not any(eb.source_id != "local_memory" for eb in final_ranked_blocks):
            validation_warnings.append("Plan required online search, but no online source files were indexed.")
            
        # Calculate retrieval confidence (0.0 to 1.0)
        confidence = 1.0
        if not final_ranked_blocks:
            confidence = 0.0
        else:
            # Avg score of top 3 evidence ranks
            top_scores = [eb.relevance_score for eb in final_ranked_blocks[:3]]
            confidence = sum(top_scores) / len(top_scores)
            
        validation_status = len(validation_errors) == 0
        validation_result = RetrievalValidationResult(
            status=validation_status,
            errors=validation_errors,
            warnings=validation_warnings,
            retrieval_confidence=round(confidence, 4)
        )

        trace_recorder.record_stage(
            "retrieval_validation",
            input_summary={"errors_count": len(validation_errors)},
            output_summary={"status": validation_status, "confidence": confidence}
        )

        # Measure times
        duration_ms = (time.perf_counter() - t0) * 1000.0
        trace_recorder.record_timing("total_retrieval_ms", duration_ms)
        
        self.retrieval_latencies.append(duration_ms)
        self.retrieval_depths.append(len(final_ranked_blocks))

        trace = trace_recorder.compile()
        return retrieval_context, validation_result, trace
