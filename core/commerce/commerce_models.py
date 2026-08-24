"""
core/commerce/commerce_models.py — Data Models & State Enums for HELIOS Commerce
================================================================================
Defines state machine enums, candidate records, comparison matrices, recommendation results,
cost breakdowns, and structured commerce execution context.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


class CommerceState(str, Enum):
    SEARCH_DISCOVERED = "SEARCH_DISCOVERED"
    PRODUCT_IDENTIFIED = "PRODUCT_IDENTIFIED"
    PRODUCT_PAGE_FOUND = "PRODUCT_PAGE_FOUND"
    DIRECT_VERIFICATION_PENDING = "DIRECT_VERIFICATION_PENDING"
    DIRECT_VERIFIED = "DIRECT_VERIFIED"
    PRICE_VERIFIED = "PRICE_VERIFIED"
    PAYMENT_ELIGIBLE = "PAYMENT_ELIGIBLE"

    DISCOVERING = "DISCOVERING"
    UNDERSTANDING = "UNDERSTANDING"
    RESEARCHING = "RESEARCHING"
    COMPARING = "COMPARING"
    RECOMMENDING = "RECOMMENDING"
    CALCULATING = "CALCULATING"
    TRANSACTION_PREPARED = "TRANSACTION_PREPARED"
    REQUIRES_AUTHORIZATION = "REQUIRES_AUTHORIZATION"
    AUTHORIZED = "AUTHORIZED"
    CHECKOUT_OPEN = "CHECKOUT_OPEN"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    MEMORY_UPDATED = "MEMORY_UPDATED"
    COMPLETED = "COMPLETED"

    # Failure / Cancellation states
    RESEARCH_FAILED = "RESEARCH_FAILED"
    RECOMMENDATION_FAILED = "RECOMMENDATION_FAILED"
    TRANSACTION_FAILED = "TRANSACTION_FAILED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    CANCELLED = "CANCELLED"


class CommerceIntentCategory(str, Enum):
    INFORMATION_ONLY = "INFORMATION_ONLY"
    PURCHASE_PREPARATION = "PURCHASE_PREPARATION"
    PURCHASE_REQUEST = "PURCHASE_REQUEST"
    PAYMENT_ONLY = "PAYMENT_ONLY"


@dataclass
class CommerceIntent:
    raw_prompt: str
    category: CommerceIntentCategory
    target_item: str
    budget_limit_inr: Optional[float] = None
    preferred_merchant: Optional[str] = None
    explicit_purchase_requested: bool = False
    explicit_no_buy: bool = False
    extracted_constraints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_prompt": self.raw_prompt,
            "category": self.category.value,
            "target_item": self.target_item,
            "budget_limit_inr": self.budget_limit_inr,
            "preferred_merchant": self.preferred_merchant,
            "explicit_purchase_requested": self.explicit_purchase_requested,
            "explicit_no_buy": self.explicit_no_buy,
            "extracted_constraints": self.extracted_constraints,
        }


@dataclass
class ProductCandidate:
    candidate_id: str
    name: str
    description: str
    price_inr: float
    merchant: str
    brand: str = ""
    source_url: str = ""
    rating: float = 4.5
    review_count: int = 100
    features: List[str] = field(default_factory=list)
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    constraints_satisfied: List[str] = field(default_factory=list)
    constraints_violated: List[str] = field(default_factory=list)
    confidence: float = 0.95
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    retrieved_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    price_type: str = "SEARCH_RESULT"  # LIVE_PRODUCT_PAGE | SEARCH_RESULT | DEMO_FIXTURE | UNKNOWN
    verification_status: str = "SEARCH_PRICE"  # DIRECT_PAGE_VERIFIED | SEARCH_PRICE | UNVERIFIED | PRICE_STALE | PRICE_CHANGED
    search_provider_used: str = "TAVILY"      # TAVILY | GOOGLE | DDGS_FALLBACK | DEMO
    freshness_status: str = "LIVE"     # LIVE (<10m) | RECENT (10m-1h) | STALE (>1h)
    merchant_offers: List[Dict[str, Any]] = field(default_factory=list)
    mrp_inr: Optional[float] = None
    selling_price_inr: Optional[float] = None
    shipping_inr: float = 0.0
    over_budget_after_delivery: bool = False
    classification: str = "DIRECT_PRODUCT_PAGE"  # DIRECT_PRODUCT_PAGE | MERCHANT_SEARCH_PAGE | MERCHANT_COLLECTION | CATEGORY_PAGE | EDITORIAL | VIDEO | FORUM | GENERAL_WEB
    evidence_score: float = 0.80
    research_quality: str = "HIGH"        # HIGH | MEDIUM | LOW
    quality_reasons: List[str] = field(default_factory=list)
    price_evidence_type: str = "SEARCH_RESULT_PRICE"  # SEARCH_RESULT_PRICE | PAGE_TEXT_PRICE | STRUCTURED_DATA_PRICE | DIRECT_VERIFIED_PRICE
    payment_eligible: bool = False
    product_identity_verified: bool = False
    direct_product_page: bool = False
    merchant_verified: bool = False
    price_verified: bool = False
    price_within_budget: bool = False
    direct_product_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "name": self.name,
            "description": self.description,
            "price_inr": self.price_inr,
            "price_paise": int(self.price_inr * 100),
            "merchant": self.merchant,
            "brand": self.brand,
            "source_url": self.source_url,
            "direct_product_url": self.direct_product_url or (self.source_url if self.classification in ("DIRECT_PRODUCT_PAGE", "PRODUCT_PAGE") else None),
            "rating": self.rating,
            "review_count": self.review_count,
            "features": self.features,
            "pros": self.pros,
            "cons": self.cons,
            "constraints_satisfied": self.constraints_satisfied,
            "constraints_violated": self.constraints_violated,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "retrieved_at": self.retrieved_at,
            "price_type": self.price_type,
            "verification_status": self.verification_status,
            "price_evidence_type": self.price_evidence_type,
            "payment_eligible": self.payment_eligible,
            "product_identity_verified": self.product_identity_verified,
            "direct_product_page": self.direct_product_page,
            "merchant_verified": self.merchant_verified,
            "price_verified": self.price_verified,
            "price_within_budget": self.price_within_budget,
            "search_provider_used": self.search_provider_used,
            "freshness_status": self.freshness_status,
            "merchant_offers": self.merchant_offers,
            "mrp_inr": self.mrp_inr,
            "selling_price_inr": self.selling_price_inr or self.price_inr,
            "shipping_inr": self.shipping_inr,
            "over_budget_after_delivery": self.over_budget_after_delivery,
            "classification": self.classification,
            "evidence_score": self.evidence_score,
            "research_quality": self.research_quality,
            "quality_reasons": self.quality_reasons,
        }


@dataclass
class ComparisonTable:
    target_item: str
    budget_limit_inr: Optional[float]
    candidates: List[ProductCandidate] = field(default_factory=list)
    best_candidate_id: Optional[str] = None
    evaluation_matrix: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_item": self.target_item,
            "budget_limit_inr": self.budget_limit_inr,
            "candidates": [c.to_dict() for c in self.candidates],
            "best_candidate_id": self.best_candidate_id,
            "evaluation_matrix": self.evaluation_matrix,
        }


@dataclass
class RecommendationResult:
    selected_candidate: ProductCandidate
    reason: str
    alternative: Optional[ProductCandidate] = None
    tradeoffs: List[str] = field(default_factory=list)
    confidence_score: float = 0.95

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_candidate": self.selected_candidate.to_dict(),
            "reason": self.reason,
            "alternative": self.alternative.to_dict() if self.alternative else None,
            "tradeoffs": self.tradeoffs,
            "confidence_score": self.confidence_score,
        }


@dataclass
class CostBreakdown:
    item_price_inr: float
    shipping_fee_inr: float = 0.0
    tax_inr: float = 0.0
    is_exact_total: bool = True
    currency: str = "INR"

    @property
    def total_inr(self) -> float:
        return round(self.item_price_inr + self.shipping_fee_inr + self.tax_inr, 2)

    @property
    def total_paise(self) -> int:
        return int(self.total_inr * 100)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_price_inr": self.item_price_inr,
            "shipping_fee_inr": self.shipping_fee_inr,
            "tax_inr": self.tax_inr,
            "total_inr": self.total_inr,
            "total_paise": self.total_paise,
            "is_exact_total": self.is_exact_total,
            "currency": self.currency,
        }


@dataclass
class CommerceContext:
    commerce_id: str
    intent: CommerceIntent
    state: CommerceState = CommerceState.DISCOVERING
    candidates: List[ProductCandidate] = field(default_factory=list)
    comparison: Optional[ComparisonTable] = None
    recommendation: Optional[RecommendationResult] = None
    cost: Optional[CostBreakdown] = None
    intent_id: Optional[str] = None
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commerce_id": self.commerce_id,
            "intent": self.intent.to_dict(),
            "state": self.state.value,
            "candidates": [c.to_dict() for c in self.candidates],
            "comparison": self.comparison.to_dict() if self.comparison else None,
            "recommendation": self.recommendation.to_dict() if self.recommendation else None,
            "cost": self.cost.to_dict() if self.cost else None,
            "intent_id": self.intent_id,
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "error_message": self.error_message,
            "created_at": self.created_at,
        }
