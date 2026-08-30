# HELIOS — TavilySearchProvider Specification

## Module Summary
- **Source File**: `core/commerce/search/tavily_search_provider.py`
- **Class**: `TavilySearchProvider(BaseSearchProvider)`
- **SDK Dependency**: `tavily-python` (`from tavily import TavilyClient`)

## Method Interface
```python
def search(
    self,
    query: str,
    *,
    max_results: int = 5,
    region: str = "IN",
    language: str = "en"
) -> SearchResponse
```

## Security & Secrets Policy
- API Key is read exclusively from `os.getenv("TAVILY_API_KEY")` or `EnvironmentManager`.
- Secrets are masked as `tvly...1234` in all telemetry, logs, and representations.
- Secrets are never hardcoded, written to Git, or exposed to LLM prompts or UI layers.

## Error Codes
| Error Code | Trigger Condition |
| :--- | :--- |
| `TAVILY_NOT_CONFIGURED` | `TAVILY_API_KEY` missing or empty in environment. |
| `TAVILY_DISABLED` | `TAVILY_SEARCH_ENABLED=false` set in `.env`. |
| `TAVILY_SDK_MISSING` | `tavily-python` package uninstalled. |
| `TAVILY_AUTH_FAILED` | HTTP 401 Unauthorized API key error from Tavily API. |
| `TAVILY_RATE_LIMITED` | HTTP 429 Monthly credit limit or rate limit exceeded. |
| `TAVILY_NETWORK_ERROR` | Connection timeout or DNS failure. |
| `TAVILY_NO_RESULTS` | Tavily returned 0 results for query. |
