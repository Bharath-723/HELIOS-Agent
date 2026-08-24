"""
HELIOS v2 - Intelligent Reasoning Core Dataclasses and Enums
Cleanly typed and immutable models.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

class TaskCategory(Enum):
    CHAT = "chat"
    FILE = "file"
    NOTES = "notes"
    SCHEDULE = "schedule"
    SEARCH = "search"
    PRIVACY_TASK = "privacy_task"
    MIXED = "mixed"

class TaskState(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class PlanningPolicy(Enum):
    LOW_RESOURCE = "low-resource"
    HIGH_ACCURACY = "high-accuracy"
    FAST_RESPONSE = "fast-response"
    PRIVACY_FIRST = "privacy-first"
    PARALLEL_FIRST = "parallel-first"

class ConstraintSeverity(Enum):
    ALLOWED = "allowed"
    PREFERRED = "preferred"
    DISCOURAGED = "discouraged"
    FORBIDDEN = "forbidden"

@dataclass(frozen=True)
class TaskIntent:
    """Parsed user intent representation."""
    primary_goal: str
    secondary_goal: Optional[str]
    category: TaskCategory
    privacy_requirement: str  # "high", "medium", "low"
    requires_internet: bool
    requires_tools: List[str]
    expected_output: str
    complexity_score: float  # 0.0 to 1.0
    urgency_level: str  # "high", "medium", "low"
    dependencies: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class TaskUnderstanding:
    """Work that must actually be performed, bridging intent and planner."""
    implicit_tasks: List[str]
    inferred_dependencies: Dict[str, List[str]]
    required_tools: List[str]
    required_resources: List[str]
    execution_constraints: List[str]
    output_expectations: Dict[str, str]

@dataclass
class AtomicTask:
    """A single atomic subtask in the execution plan."""
    task_id: str
    description: str
    expected_output: str
    required_tool: Optional[str]
    required_model: str
    fallback_strategy: str
    estimated_cost: float
    estimated_latency_ms: float
    estimated_risk: float
    dependencies: List[str] = field(default_factory=list)
    state: TaskState = TaskState.PENDING
    execution_result: Optional[str] = None
    
    # Sprint 1.5 Additions (Backward compatible)
    priority: int = 1
    estimated_tokens: int = 0
    retry_limit: int = 3
    verification_required: bool = False
    cacheable: bool = True
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    failure_mode: str = "abort"  # "abort", "retry", "ignore"
    timeout: float = 60.0
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    execution_constraints: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class ExecutionGraph:
    """DAG structure representing atomic tasks and relationships."""
    tasks: Dict[str, AtomicTask]
    execution_order: List[str]  # Topological sort
    parallel_groups: List[List[str]]  # Groups of task IDs that can execute concurrently
    fallback_nodes: Dict[str, str]  # Map task_id -> fallback task_id
    retry_policies: Dict[str, int]  # Map task_id -> max_retries
    verification_checks: List[str]  # List of verification rules/assertions to run post-execution

@dataclass(frozen=True)
class ReasoningContext:
    """Local and global system parameters used during reasoning."""
    conversation_history: List[Dict[str, str]]
    memory_references: List[str]
    available_tools: List[str]
    available_models: List[str]
    system_state: Dict[str, Any]
    hardware_specs: Dict[str, Any]
    internet_available: bool
    local_model_available: bool
    privacy_constraints_active: bool

@dataclass(frozen=True)
class PlanExplanation:
    """Structured explainability object detailing planning decisions."""
    why_tasks_exist: Dict[str, str]
    why_ordering_exists: List[str]
    why_dependencies_exist: Dict[str, List[str]]
    why_internet_required: str
    why_privacy_required: str
    why_tools_selected: Dict[str, str]
    why_models_suggested: Dict[str, str]

@dataclass(frozen=True)
class ValidationResult:
    """Planning validation outcomes."""
    status: bool  # True if valid, False if invalid
    errors: List[str]
    warnings: List[str]
    validation_summary: str

@dataclass(frozen=True)
class StrategyEvaluation:
    """Calculated planning metrics and scores for an alternative strategy."""
    cost: float
    latency: float
    complexity: float
    parallel_efficiency: float
    failure_probability: float
    privacy_score: float
    tool_utilization: float
    utility_score: float
    utility_breakdown: Dict[str, float] = field(default_factory=dict)

@dataclass(frozen=True)
class PlanningStrategy:
    """An alternative execution plan candidate before final selection."""
    name: str
    policy: PlanningPolicy
    graph: ExecutionGraph
    fingerprint: str
    complexity_metrics: Dict[str, Any]
    evaluation_metrics: StrategyEvaluation
    constraints_status: Dict[str, ConstraintSeverity] = field(default_factory=dict)

@dataclass(frozen=True)
class SelectionDecision:
    """Decision details for the selected optimal strategy."""
    selected_strategy_name: str
    ranking_table: List[Dict[str, Any]]
    advantages: List[str]
    disadvantages: List[str]
    selection_explanation: str
    rejected_explanations: Dict[str, str]
    selection_margin: float
    selection_confidence: float

@dataclass(frozen=True)
class PlanningTrace:
    """Detailed reasoning trace of the adaptive planning process."""
    stages: Dict[str, Any]  # Tracks inputs and outputs for each step in pipeline
    all_strategies: List[str]  # Generated plan names
    filtered_strategies: List[str]  # Remaining plan names after constraints
    ranked_strategies: List[Dict[str, Any]]  # Plan names and utility scores
    selected_strategy_name: str
    decision_rationale: str
    planning_duration_ms: float

@dataclass(frozen=True)
class PlanOptimizationMetrics:
    """Calculated metrics representing optimization gains."""
    gain: float
    latency_reduction_ms: float
    complexity_reduction: float
    dependency_reduction: int
    parallelism_increase: float
    cost_savings: float
    utility_improvement: float

@dataclass(frozen=True)
class OptimizationHistoryNode:
    """Record of a single refinement loop transformation."""
    iteration: int
    fingerprint: str
    graph: ExecutionGraph
    utility: float
    decision_taken: str

@dataclass(frozen=True)
class PlanOptimizationTrace:
    """Trace history of plan optimizations."""
    original_fingerprint: str
    final_fingerprint: str
    original_utility: float
    final_utility: float
    history: List[OptimizationHistoryNode]
    optimization_confidence: float
    metrics: PlanOptimizationMetrics

@dataclass(frozen=True)
class ExecutionPlan:
    """The final completed execution strategy compiled by the planning engine."""
    plan_id: str
    prompt: str
    intent: TaskIntent
    understanding: TaskUnderstanding
    context: ReasoningContext
    graph: ExecutionGraph
    explanation: PlanExplanation
    complexity_metrics: Dict[str, Any]
    validation_result: ValidationResult
    trace: PlanningTrace
    selection: SelectionDecision
    optimization_trace: Optional[PlanOptimizationTrace]
    planning_time_ms: float
    planning_confidence: float
    decision_path_summary: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
