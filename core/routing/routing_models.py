from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class RoutingDecision(Enum):
    LOCAL = "LOCAL"
    CLOUD = "CLOUD"
    NO_DECISION = "NO_DECISION"

class ConstraintDecision(Enum):
    FORCE_LOCAL = "FORCE_LOCAL"
    FORCE_CLOUD = "FORCE_CLOUD"
    NONE = "NONE"

@dataclass
class RoutingContext:
    prompt: str
    parsed_intent: Optional[str] = None
    timestamp: str = ""
    internet_available: bool = True
    local_model_available: bool = True
    cloud_available: bool = True
    active_local_model: str = ""
    active_cloud_model: str = ""
    operating_system: str = "Windows"
    cpu_percent: float = 0.0
    ram_available_mb: float = 0.0
    gpu_available: bool = False
    gpu_memory_mb: float = 0.0

@dataclass
class RoutingFeatures:
    privacy_score: float = 0.0         # 0.0 to 1.0 (acts as privacy_required)
    freshness_score: float = 0.0       # 0.0 to 1.0 (acts as freshness_required)
    complexity_score: float = 0.0      # 0.0 to 1.0 (acts as complexity_required)
    hardware_score: float = 0.0        # 0.0 to 1.0
    latency_score: float = 0.0         # 0.0 to 1.0
    cost_score: float = 0.0            # 0.0 to 1.0
    requires_internet: bool = False
    contains_local_data: bool = False
    contains_sensitive_data: bool = False
    estimated_tokens: int = 0
    estimated_execution: float = 0.0   # seconds
    reasoning: str = ""

@dataclass
class RoutingExplanation:
    decision: RoutingDecision
    reasons: List[str] = field(default_factory=list)
    feature_values: Dict[str, Any] = field(default_factory=dict)
    constraints_triggered: List[str] = field(default_factory=list)
    timestamp: str = ""
    selected_model: str = ""
    confidence: float = 0.0
    rejected_alternatives: List[str] = field(default_factory=list)

@dataclass
class DecisionTrace:
    extracted_features: Dict[str, Any]
    triggered_constraints: List[str]
    local_score: float
    cloud_score: float
    routing_decision: str
    confidence: float
    score_breakdown: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RoutingResult:
    decision: RoutingDecision
    features: RoutingFeatures
    context: RoutingContext
    scores: Dict[str, float] = field(default_factory=dict)
    explanation: RoutingExplanation = None  # type: ignore
    execution_time_ms: float = 0.0
    selected_model: str = ""
    constraints_triggered: List[str] = field(default_factory=list)
    algorithm_name: str = "CAHRA"
    algorithm_version: str = "CAHRA-v1.0"
    strategy_name: str = "Capability-Aware Weighted Hybrid Routing"
    decision_trace: Optional[DecisionTrace] = None
