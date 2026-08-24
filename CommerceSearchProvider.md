# HELIOS — Search Provider Interface Specification

## Data Models

### SearchResult
- `title`: Product listing title
- `url`: Direct source URI
- `snippet`: Listing description snippet
- `domain`: Merchant domain (e.g. `amazon.in`, `flipkart.com`, `croma.com`)
- `source`: Merchant name
- `retrieved_at`: ISO timestamp
- `provider`: Provider ID (`GOOGLE` or `DDGS_FALLBACK`)
- `confidence`: Heuristic reliability float
- `result_type`: `SEARCH_RESULT` or `LIVE_PRODUCT_PAGE`

### SearchResponse
- `query`: Dynamic search query
- `results`: List of `SearchResult` objects
- `provider_used`: Provider ID
- `execution_time_ms`: Search latency in milliseconds
- `error_message`: Error details if search fails
