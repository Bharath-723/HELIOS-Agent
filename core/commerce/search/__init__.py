"""
core/commerce/search/__init__.py — Provider-Abstracted Web Research Subsystem
=============================================================================
Tavily-First Primary Commerce Research Subsystem with Result Classification & DDGS Fallback.
"""

from core.commerce.search.search_models import SearchResult, SearchResponse
from core.commerce.search.base_search_provider import BaseSearchProvider
from core.commerce.search.tavily_search_provider import TavilySearchProvider
from core.commerce.search.google_search_provider import GoogleSearchProvider
from core.commerce.search.fallback_search_provider import DDGSSearchProvider
from core.commerce.search.result_classifier import ResultClassifier

__all__ = [
    "SearchResult",
    "SearchResponse",
    "BaseSearchProvider",
    "TavilySearchProvider",
    "GoogleSearchProvider",
    "DDGSSearchProvider",
    "ResultClassifier",
]
