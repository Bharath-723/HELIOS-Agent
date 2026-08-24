"""
core/commerce/search/fallback_search_provider.py — DDGS Fallback Search Provider
===================================================================================
Fallback web research provider utilizing ddgs library, identifying as DDGS_FALLBACK.
"""

import time
import logging
from urllib.parse import urlparse
from core.commerce.search.base_search_provider import BaseSearchProvider
from core.commerce.search.search_models import SearchResponse, SearchResult

log = logging.getLogger("helios.commerce.search.fallback")


class DDGSSearchProvider(BaseSearchProvider):
    """Fallback search provider using ddgs."""

    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        region: str = "IN",
        language: str = "en"
    ) -> SearchResponse:
        start_time = time.time()
        log.info("DDGSSearchProvider: Executing fallback search for '%s'", query)

        try:
            from ddgs import DDGS
        except ImportError:
            log.error("DDGSSearchProvider: ddgs package unavailable.")
            return SearchResponse(
                query=query,
                results=[],
                provider_used="DDGS_FALLBACK",
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message="ddgs package import error"
            )

        try:
            raw_results = []
            with DDGS() as d:
                res = list(d.text(query, max_results=max_results))
                for item in res:
                    raw_results.append(item)

            search_results = []
            for item in raw_results:
                title = item.get("title", "").strip()
                href = item.get("href", "").strip()
                snippet = item.get("body", "").strip()
                domain = urlparse(href).netloc if href else "web"

                search_results.append(SearchResult(
                    title=title,
                    url=href,
                    snippet=snippet,
                    domain=domain,
                    source=domain,
                    provider="DDGS_FALLBACK",
                    confidence=0.90,
                    result_type="SEARCH_RESULT"
                ))

            elapsed = (time.time() - start_time) * 1000
            log.info("DDGSSearchProvider: Retrieved %d results in %.1f ms", len(search_results), elapsed)
            return SearchResponse(
                query=query,
                results=search_results,
                provider_used="DDGS_FALLBACK",
                execution_time_ms=elapsed
            )

        except Exception as exc:
            elapsed = (time.time() - start_time) * 1000
            log.error("DDGSSearchProvider execution failed: %s", exc)
            return SearchResponse(
                query=query,
                results=[],
                provider_used="DDGS_FALLBACK",
                execution_time_ms=elapsed,
                error_message=str(exc)
            )
