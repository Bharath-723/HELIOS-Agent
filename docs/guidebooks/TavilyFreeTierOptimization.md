# HELIOS — Tavily Free-Tier Credit Optimization Strategy

## Optimization Rules
1. **Query Bounding**: Maximum **2 high-quality queries** generated per commerce request (e.g., `"{target} under ₹{budget} India"` and `"{target} price Amazon India Flipkart Croma"`).
2. **Session Caching**: `TavilySearchProvider` caches `(query, max_results)` requests in memory during active session to eliminate duplicate API requests.
3. **Default Parameters**: Uses `search_depth="basic"`, `max_results=5`, `include_answer=False`, `include_raw_content=False` to preserve credits.
4. **Targeted Domain Filtering**: Filters for Indian merchants (`amazon.in`, `flipkart.com`, `croma.com`, `reliancedigital.in`, `vijaysales.com`, `myntra.com`, `tatacliq.com`).
5. **No Conversational Overhead**: Normal non-commerce chat ("Hi", "What is Python?") never invokes Tavily search.
