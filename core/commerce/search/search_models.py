"""
core/commerce/search/search_models.py — Search Telemetry & Data Models
========================================================================
Defines normalized search results, provider attribution, and structured responses.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    domain: str
    source: str
    retrieved_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    provider: str = "GOOGLE"  # GOOGLE | TAVILY | DDGS_FALLBACK
    confidence: float = 0.95
    result_type: str = "SEARCH_RESULT"  # SEARCH_RESULT | LIVE_PRODUCT_PAGE
    classification: str = "GENERAL_WEB"  # PRODUCT_PAGE | MERCHANT_COLLECTION | EDITORIAL | VIDEO | FORUM | GENERAL_WEB
    evidence_score: float = 0.50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "domain": self.domain,
            "source": self.source,
            "retrieved_at": self.retrieved_at,
            "provider": self.provider,
            "confidence": self.confidence,
            "result_type": self.result_type,
            "classification": self.classification,
            "evidence_score": self.evidence_score,
        }


@dataclass
class SearchResponse:
    query: str
    results: List[SearchResult] = field(default_factory=list)
    provider_used: str = "GOOGLE"
    execution_time_ms: float = 0.0
    success: bool = True
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    fallback_allowed: bool = True
    retrieved_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "provider_used": self.provider_used,
            "execution_time_ms": self.execution_time_ms,
            "success": self.success,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "fallback_allowed": self.fallback_allowed,
            "retrieved_at": self.retrieved_at,
        }
