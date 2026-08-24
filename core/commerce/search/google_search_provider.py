"""
core/commerce/search/google_search_provider.py — Primary Google Search Provider
==================================================================================
Primary web research provider using official google-genai SDK Search Grounding
and optional Google Custom Search REST API fallback.
Loads credentials strictly from environment variables (GOOGLE_API_KEY / GEMINI_API_KEY).
Never hardcodes or exposes secrets.
"""

import os
import time
import logging
from urllib.parse import urlparse
from typing import Optional, List, Tuple, Any

from core.commerce.search.base_search_provider import BaseSearchProvider
from core.commerce.search.search_models import SearchResponse, SearchResult

log = logging.getLogger("helios.commerce.search.google")


class GoogleSearchProvider(BaseSearchProvider):
    """Primary Google Search Provider using google-genai Search Grounding / Custom Search REST API."""

    SUPPORTED_MODELS = [
        os.getenv("GOOGLE_SEARCH_MODEL", "gemini-3.6-flash"),
        "gemini-flash-latest",
        "gemini-3.5-flash",
        "gemini-3.7-flash",
        "gemini-1.5-flash"
    ]

    def __init__(self, api_key: Optional[str] = None) -> None:
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = (
                os.getenv("GOOGLE_API_KEY")
                or os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_CLOUD_API_KEY")
                or ""
            )
        self.enabled = os.getenv("GOOGLE_SEARCH_ENABLED", "true").lower() == "true"
        self.cx = os.getenv("GOOGLE_SEARCH_CX", "").strip()
        self.diagnostic_only = os.getenv("GOOGLE_SEARCH_DIAGNOSTIC_ONLY", "false").lower() == "true"

    def is_available(self) -> bool:
        return bool(self.enabled and self.api_key and len(self.api_key.strip()) > 5)

    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        region: str = "IN",
        language: str = "en"
    ) -> SearchResponse:
        start_time = time.time()
        fallback_allowed = not self.diagnostic_only

        log.info("[COMMERCE SEARCH] provider=GOOGLE enabled=%s credential_configured=%s diagnostic_only=%s query='%s'",
                 self.enabled, bool(self.api_key), self.diagnostic_only, query)

        if not self.enabled:
            return SearchResponse(
                query=query,
                results=[],
                provider_used="GOOGLE",
                execution_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_code="GOOGLE_DISABLED",
                error_message="Google Search is disabled via GOOGLE_SEARCH_ENABLED=false.",
                fallback_allowed=fallback_allowed
            )

        if not self.is_available():
            return SearchResponse(
                query=query,
                results=[],
                provider_used="GOOGLE",
                execution_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_code="GOOGLE_NOT_CONFIGURED",
                error_message="GOOGLE_API_KEY / GEMINI_API_KEY not configured in environment.",
                fallback_allowed=fallback_allowed
            )

        # ── Primary Mechanism: Official google-genai SDK Search Grounding ──────
        try:
            from google import genai
            from google.genai import types
        except ImportError as imp_err:
            log.warning("google-genai SDK not available: %s", imp_err)
            # Try REST fallback if configured
            return self._try_custom_search_rest(query, max_results, region, language, start_time, fallback_allowed,
                                               sdk_error="GOOGLE_SDK_MISSING")

        # Select compatible model & execute search grounding with bounded retry
        client = genai.Client(api_key=self.api_key)
        last_error_code = "GOOGLE_REQUEST_FAILED"
        last_error_msg = "Unknown error"

        # Unique list of model candidates
        candidate_models = []
        for m in self.SUPPORTED_MODELS:
            if m and m not in candidate_models:
                candidate_models.append(m)

        for model_name in candidate_models:
            log.info("[COMMERCE SEARCH] Attempting Gemini Search Grounding model='%s'...", model_name)
            
            # Bounded retry: max 1 retry for transient errors
            max_attempts = 2
            for attempt in range(max_attempts):
                try:
                    config = types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                    prompt = (
                        f"Search Google for current product price, store URL, and merchant availability in India: '{query}'. "
                        f"Provide accurate INR price listings and store links."
                    )
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )

                    results = self._parse_genai_grounding_response(response, query, max_results)
                    elapsed = (time.time() - start_time) * 1000

                    if results:
                        log.info("[COMMERCE SEARCH] provider=GOOGLE success=true model=%s results=%d latency=%.1fms",
                                 model_name, len(results), elapsed)
                        return SearchResponse(
                            query=query,
                            results=results,
                            provider_used="GOOGLE",
                            execution_time_ms=elapsed,
                            success=True,
                            error_code=None,
                            error_message=None,
                            fallback_allowed=fallback_allowed
                        )
                    else:
                        last_error_code = "GOOGLE_EMPTY_RESULTS"
                        last_error_msg = f"Model {model_name} returned response but zero grounding chunks parsed."
                        break  # Try next model if zero chunks

                except Exception as exc:
                    exc_str = str(exc)
                    if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str or "quota" in exc_str.lower():
                        log.warning("[COMMERCE SEARCH] provider=GOOGLE model=%s status=429 RESOURCE_EXHAUSTED", model_name)
                        last_error_code = "GOOGLE_RATE_LIMITED"
                        last_error_msg = f"Google Gemini API quota/rate limit exceeded (429): {exc_str[:120]}"
                        # Quota error is immediate, no point retrying same key
                        break
                    elif "404" in exc_str or "NOT_FOUND" in exc_str:
                        log.info("[COMMERCE SEARCH] provider=GOOGLE model=%s 404 NOT_FOUND. Trying next model candidate.", model_name)
                        last_error_code = "GOOGLE_MODEL_NOT_FOUND"
                        last_error_msg = f"Model {model_name} not available (404)."
                        break
                    elif "401" in exc_str or "403" in exc_str or "API_KEY_INVALID" in exc_str:
                        log.error("[COMMERCE SEARCH] provider=GOOGLE status=401/403 Auth Failure.")
                        last_error_code = "GOOGLE_AUTH_FAILED"
                        last_error_msg = f"Google API authentication failure: {exc_str[:120]}"
                        break
                    else:
                        log.warning("[COMMERCE SEARCH] Gemini call attempt %d failed for model %s: %s", attempt + 1, model_name, exc_str[:120])
                        last_error_code = "GOOGLE_REQUEST_FAILED"
                        last_error_msg = exc_str[:150]
                        if attempt < max_attempts - 1:
                            time.sleep(0.5)

        # If Search Grounding fails or hits rate limits, try Custom Search REST if configured
        return self._try_custom_search_rest(
            query, max_results, region, language, start_time, fallback_allowed,
            fallback_code=last_error_code, fallback_msg=last_error_msg
        )

    def _parse_genai_grounding_response(self, response: Any, query: str, max_results: int) -> List[SearchResult]:
        results: List[SearchResult] = []
        if not hasattr(response, 'candidates') or not response.candidates:
            return results

        candidate = response.candidates[0]
        if not hasattr(candidate, 'grounding_metadata') or not candidate.grounding_metadata:
            return results

        g_meta = candidate.grounding_metadata
        chunks = getattr(g_meta, 'grounding_chunks', None) or []
        resp_snippet = getattr(response, 'text', '') or ""

        for chunk in chunks[:max_results]:
            web = getattr(chunk, 'web', None)
            if web:
                title = getattr(web, 'title', query) or query
                url = getattr(web, 'uri', '') or ""
                domain = urlparse(url).netloc if url else "google.com"
                
                results.append(SearchResult(
                    title=title,
                    url=url,
                    snippet=resp_snippet[:200],
                    domain=domain,
                    source=domain,
                    provider="GOOGLE",
                    confidence=0.98,
                    result_type="SEARCH_RESULT"
                ))

        return results

    def _try_custom_search_rest(
        self,
        query: str,
        max_results: int,
        region: str,
        language: str,
        start_time: float,
        fallback_allowed: bool,
        fallback_code: str = "GOOGLE_REQUEST_FAILED",
        fallback_msg: str = "Search grounding failed",
        sdk_error: Optional[str] = None
    ) -> SearchResponse:
        """Executes Custom Search JSON REST API if GOOGLE_SEARCH_CX is configured."""
        if sdk_error:
            fallback_code = sdk_error

        if not self.cx or self.cx in ("not_set", "search_engine_cx", ""):
            elapsed = (time.time() - start_time) * 1000
            final_code = "GOOGLE_CX_NOT_CONFIGURED" if fallback_code == "GOOGLE_REQUEST_FAILED" else fallback_code
            log.info("[COMMERCE SEARCH] Custom Search REST skipped (GOOGLE_SEARCH_CX not configured). Returning status=%s", final_code)
            return SearchResponse(
                query=query,
                results=[],
                provider_used="GOOGLE",
                execution_time_ms=elapsed,
                success=False,
                error_code=final_code,
                error_message=fallback_msg,
                fallback_allowed=fallback_allowed
            )

        log.info("[COMMERCE SEARCH] Attempting secondary Custom Search REST API (CX=%s...)...", self.cx[:4])
        try:
            import requests
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": self.cx,
                "q": query,
                "num": min(max_results, 10),
                "gl": region.lower(),
                "hl": language
            }
            resp = requests.get(url, params=params, timeout=4.0)
            elapsed = (time.time() - start_time) * 1000

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                results = []
                for item in items[:max_results]:
                    item_url = item.get("link", "")
                    domain = urlparse(item_url).netloc if item_url else "google.com"
                    results.append(SearchResult(
                        title=item.get("title", query),
                        url=item_url,
                        snippet=item.get("snippet", ""),
                        domain=domain,
                        source=domain,
                        provider="GOOGLE_CUSTOM_SEARCH",
                        confidence=0.97,
                        result_type="SEARCH_RESULT"
                    ))

                if results:
                    log.info("[COMMERCE SEARCH] provider=GOOGLE_CUSTOM_SEARCH success=true results=%d latency=%.1fms", len(results), elapsed)
                    return SearchResponse(
                        query=query,
                        results=results,
                        provider_used="GOOGLE_CUSTOM_SEARCH",
                        execution_time_ms=elapsed,
                        success=True,
                        error_code=None,
                        error_message=None,
                        fallback_allowed=fallback_allowed
                    )

            err_code = "GOOGLE_CUSTOM_SEARCH_FORBIDDEN" if resp.status_code == 403 else f"GOOGLE_REST_HTTP_{resp.status_code}"
            log.warning("[COMMERCE SEARCH] Custom Search REST failed with status %d (%s): %s", resp.status_code, err_code, resp.text[:120])
            return SearchResponse(
                query=query,
                results=[],
                provider_used="GOOGLE_CUSTOM_SEARCH",
                execution_time_ms=elapsed,
                success=False,
                error_code=err_code,
                error_message=f"Custom Search REST status {resp.status_code}: {resp.text[:100]}",
                fallback_allowed=fallback_allowed
            )

        except Exception as exc:
            elapsed = (time.time() - start_time) * 1000
            log.error("[COMMERCE SEARCH] Custom Search REST call exception: %s", exc)
            return SearchResponse(
                query=query,
                results=[],
                provider_used="GOOGLE_CUSTOM_SEARCH",
                execution_time_ms=elapsed,
                success=False,
                error_code="GOOGLE_REST_EXCEPTION",
                error_message=str(exc),
                fallback_allowed=fallback_allowed
            )
