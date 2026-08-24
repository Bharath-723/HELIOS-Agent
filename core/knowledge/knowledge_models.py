"""
HELIOS v2 - Knowledge, Memory & Retrieval Intelligence Dataclasses
Cleanly typed and immutable models.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

class MemoryLayer(Enum):
    L1_WORKING = "L1_WORKING"
    L2_SESSION = "L2_SESSION"
    L3_PERSISTENT = "L3_PERSISTENT"
    L4_KNOWLEDGE = "L4_KNOWLEDGE"

class VerificationStatus(Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    SUSPICIOUS = "suspicious"

@dataclass(frozen=True)
class MemoryEntry:
    """A single fact or record stored in hierarchical memory."""
    entry_id: str
    layer: MemoryLayer
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    priority: int = 1  # 1 (low) to 5 (high)

@dataclass(frozen=True)
class MemorySearchQuery:
    """Structure for deterministic memory scans."""
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata_filter: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    min_priority: int = 1

@dataclass(frozen=True)
class KnowledgeSource:
    """An external or local file/database index source."""
    source_id: str
    name: str
    source_type: str  # "file", "note", "url", "database"
    uri: str
    version: str
    last_modified: float
    freshness_status: str  # "fresh", "stale", "expired"
    reliability_score: float = 1.0  # 0.0 to 1.0
    verification_status: VerificationStatus = VerificationStatus.VERIFIED

@dataclass(frozen=True)
class RetrievalTask:
    """An atomic retrieval action in a retrieval plan."""
    task_id: str
    source_layer: MemoryLayer
    query: str
    priority: int
    estimated_latency_ms: float
    estimated_cost: float

@dataclass(frozen=True)
class RetrievalPlan:
    """Execution strategy mapping what and where to retrieve."""
    original_plan_id: str
    tasks: List[RetrievalTask]
    cost_estimate: float
    latency_estimate: float

@dataclass(frozen=True)
class EvidenceBlock:
    """A raw block of evidence retrieved from memory or sources."""
    source_id: str
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    source_reliability: float
    timestamp: float
    final_evidence_rank: int = 0

@dataclass(frozen=True)
class RetrievalValidationResult:
    """Retrieval validation outcomes."""
    status: bool  # True if valid, False if invalid
    errors: List[str]
    warnings: List[str]
    retrieval_confidence: float

@dataclass(frozen=True)
class RetrievalContext:
    """The final assembled context passed back to the reasoning/routing plane."""
    context_id: str
    conversation_history: List[Dict[str, str]]
    evidence_blocks: List[EvidenceBlock]
    constraints_active: List[str]
    assembled_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass(frozen=True)
class CacheEntry:
    """A cached entry inside the knowledge lookup cache."""
    key: str
    data: Any
    expiry_timestamp: float
    access_count: int = 0
    cache_hits: int = 0

@dataclass(frozen=True)
class KnowledgeStats:
    """Telemetry statistics tracking knowledge subsystem usage."""
    hit_ratio: float
    average_retrieval_latency_ms: float
    memory_utilization_bytes: int
    knowledge_coverage: float
    average_retrieval_depth: float
    memory_distribution: Dict[str, int]

@dataclass(frozen=True)
class RetrievalTrace:
    """Stage-preserving log details of the retrieval process."""
    stages: Dict[str, Any]
    search_decisions: List[str]
    timings_ms: Dict[str, float]
    cache_hits: List[str]

@dataclass(frozen=True)
class KnowledgeGraphNode:
    """A node representing an entity in the Knowledge Graph."""
    node_id: str
    entity_type: str
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class KnowledgeGraphEdge:
    """A directed edge representing relations in the Knowledge Graph."""
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source_verification_ref: str = ""

@dataclass(frozen=True)
class KnowledgeGraph:
    """Graph database topology mapping entity relations."""
    nodes: Dict[str, KnowledgeGraphNode] = field(default_factory=dict)
    edges: List[KnowledgeGraphEdge] = field(default_factory=list)
