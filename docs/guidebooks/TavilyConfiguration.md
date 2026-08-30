# HELIOS — Tavily Environment & Subsystem Configuration

## Environment Variables
The following environment variables control Tavily commerce search in `.env`:

```ini
# Tavily Primary Commerce Search
TAVILY_API_KEY=your_tavily_api_key_here
TAVILY_SEARCH_ENABLED=true
COMMERCE_SEARCH_PROVIDER=tavily

# Optional Google Search
GOOGLE_SEARCH_ENABLED=false
```

## Provider Modes (`COMMERCE_SEARCH_PROVIDER`)
1. **`tavily`** *(Default)*: TavilySearchProvider -> DDGSSearchProvider.
2. **`auto`**: TavilySearchProvider -> GoogleSearchProvider -> DDGSSearchProvider.
3. **`google`**: GoogleSearchProvider -> DDGSSearchProvider.
4. **`ddgs`**: DDGSSearchProvider directly.
