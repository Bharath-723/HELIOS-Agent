"""
core/commerce/search/base_search_provider.py — Abstract Search Provider Interface
===================================================================================
Base class defining the unified search interface for all web research engines.
"""

from abc import ABC, abstractmethod
from core.commerce.search.search_models import SearchResponse


class BaseSearchProvider(ABC):
    """Abstract search provider base interface."""

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        region: str = "IN",
        language: str = "en"
    ) -> SearchResponse:
        """Executes search and returns normalized SearchResponse."""
        pass
