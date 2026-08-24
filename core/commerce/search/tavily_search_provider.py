"""
core/commerce/search/tavily_search_provider.py — Primary Tavily Commerce Search Provider
========================================================================================
Primary web research provider using official Tavily Python SDK (tavily-python).
Loads credentials strictly from environment variables (TAVILY_API_KEY).
Never hardcodes or exposes secrets.
"""

import os
import re
import time
import logging
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any

from core.commerce.search.base_search_provider import BaseSearchProvider
from core.commerce.search.search_models import SearchResponse, SearchResult

log = logging.getLogger("helios.commerce.search.tavily")


class TavilySearchProvider(BaseSearchProvider):
    """Primary Tavily Commerce Search Provider with Session Caching & Free-Tier Optimization."""

    _cache: Dict[str, SearchResponse] = {}

    def __init__(self, api_key: Optional[str] = None) -> None:
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("TAVILY_API_KEY", "").strip()
            
        self.enabled = os.getenv("TAVILY_SEARCH_ENABLED", "true").lower() == "true"
        self.diagnostic_only = os.getenv("COMMERCE_SEARCH_DIAGNOSTIC_ONLY", "false").lower() == "true"

    def is_available(self) -> bool:
        return bool(self.enabled and self.api_key and len(self.api_key.strip()) > 5)

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        region: str = "IN",
        language: str = "en"
    ) -> SearchResponse:
        start_time = time.time()
        fallback_allowed = not self.diagnostic_only
        cache_key = f"{query.strip().lower()}:{max_results}:{region}"

        # ── 1. Check Session Cache ──────────────────────────────────────────
        if cache_key in self._cache:
            log.info("[COMMERCE SEARCH] provider=TAVILY cached=true query='%s'", query)
            cached_resp = self._cache[cache_key]
            return cached_resp

        masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) >= 8 else ("CONFIGURED" if self.api_key else "MISSING")
        log.info("[COMMERCE SEARCH] provider=TAVILY enabled=%s credential=%s query='%s'",
                 self.enabled, masked_key, query)

        if not self.enabled:
            return SearchResponse(
                query=query,
                results=[],
                provider_used="TAVILY",
                execution_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_code="TAVILY_DISABLED",
                error_message="Tavily Search is disabled via TAVILY_SEARCH_ENABLED=false.",
                fallback_allowed=fallback_allowed
            )

        if not self.is_available():
            return SearchResponse(
                query=query,
                results=[],
                provider_used="TAVILY",
                execution_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_code="TAVILY_NOT_CONFIGURED",
                error_message="TAVILY_API_KEY not configured in environment.",
                fallback_allowed=fallback_allowed
            )

        # ── 2. SDK Availability Check ────────────────────────────────────────
        try:
            from tavily import TavilyClient
        except ImportError as imp_err:
            log.error("TavilySearchProvider: tavily-python package import failed: %s", imp_err)
            return SearchResponse(
                query=query,
                results=[],
                provider_used="TAVILY",
                execution_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_code="TAVILY_SDK_MISSING",
                error_message="tavily-python SDK package not installed.",
                fallback_allowed=fallback_allowed
            )

        # ── 3. Execute Search Request ─────────────────────────────────────────
        try:
            client = TavilyClient(api_key=self.api_key)
            
            # Prioritize Indian commerce domains if India region specified
            domains_filter = [
                "amazon.in", "flipkart.com", "croma.com",
                "reliancedigital.in", "vijaysales.com", "myntra.com", "tatacliq.com"
            ]

            response_data = client.search(
                query=query,
                search_depth="basic",
                max_results=min(max_results, 5),
                topic="general",
                include_answer=False,
                include_raw_content=False,
                include_domains=domains_filter if "india" in query.lower() or region.upper() == "IN" else None
            )

            results_list = response_data.get("results", [])
            
            # If domain filter returned 0, retry without domain filter to avoid missing available sellers
            if not results_list and "india" in query.lower():
                log.info("TavilySearchProvider: Domain-filtered search returned 0. Retrying broader search.")
                response_data = client.search(
                    query=query,
                    search_depth="basic",
                    max_results=min(max_results, 5),
                    topic="general",
                    include_answer=False,
                    include_raw_content=False
                )
                results_list = response_data.get("results", [])

            from core.commerce.search.result_classifier import ResultClassifier

            elapsed = (time.time() - start_time) * 1000
            normalized_results: List[SearchResult] = []

            for item in results_list:
                item_url = item.get("url", "").strip()
                title = item.get("title", query).strip()
                snippet = item.get("content", "").strip()
                score = float(item.get("score", 0.95))
                domain = urlparse(item_url).netloc if item_url else "tavily.com"

                classification = ResultClassifier.classify(item_url, title, snippet)
                has_price = bool(re.search(r'₹\s*\d+', snippet) or re.search(r'rs\.?\s*\d+', snippet, re.I))
                ev_score = ResultClassifier.calculate_evidence_score(classification, domain, has_price, score)

                normalized_results.append(SearchResult(
                    title=title,
                    url=item_url,
                    snippet=snippet,
                    domain=domain,
                    source="TAVILY",
                    provider="TAVILY",
                    confidence=min(max(score, 0.5), 0.99),
                    result_type="SEARCH_RESULT",
                    classification=classification,
                    evidence_score=ev_score
                ))

            if normalized_results:
                log.info("[COMMERCE SEARCH] provider=TAVILY success=true results=%d latency=%.1fms",
                         len(normalized_results), elapsed)
                resp = SearchResponse(
                    query=query,
                    results=normalized_results,
                    provider_used="TAVILY",
                    execution_time_ms=elapsed,
                    success=True,
                    error_code=None,
                    error_message=None,
                    fallback_allowed=fallback_allowed
                )
                # Store in session cache
                self._cache[cache_key] = resp
                return resp
            else:
                log.warning("[COMMERCE SEARCH] provider=TAVILY success=false error=TAVILY_NO_RESULTS")
                return SearchResponse(
                    query=query,
                    results=[],
                    provider_used="TAVILY",
                    execution_time_ms=elapsed,
                    success=False,
                    error_code="TAVILY_NO_RESULTS",
                    error_message="Tavily search returned 0 results.",
                    fallback_allowed=fallback_allowed
                )

        except Exception as exc:
            elapsed = (time.time() - start_time) * 1000
            exc_str = str(exc)
            
            error_code = "TAVILY_UNKNOWN_ERROR"
            if "401" in exc_str or "unauthorized" in exc_str.lower() or "invalid api key" in exc_str.lower():
                error_code = "TAVILY_AUTH_FAILED"
            elif "429" in exc_str or "rate limit" in exc_str.lower() or "quota" in exc_str.lower():
                error_code = "TAVILY_RATE_LIMITED"
            elif "connection" in exc_str.lower() or "timeout" in exc_str.lower():
                error_code = "TAVILY_NETWORK_ERROR"

            log.error("[COMMERCE SEARCH] provider=TAVILY success=false error=%s msg='%s'", error_code, exc_str[:120])

            return SearchResponse(
                query=query,
                results=[],
                provider_used="TAVILY",
                execution_time_ms=elapsed,
                success=False,
                error_code=error_code,
                error_message=exc_str[:150],
                fallback_allowed=fallback_allowed
            )

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()
