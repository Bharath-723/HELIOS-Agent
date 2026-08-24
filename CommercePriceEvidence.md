# HELIOS — Commerce Price Evidence & Attribution

## Evidence Attributes

Every commercial recommendation includes explicit evidence:
- **Discovered Price**: Extracted INR price with source merchant name.
- **Verification Status**: `DIRECT_PAGE_VERIFIED` vs `SEARCH_PRICE`.
- **Search Provider Attribution**: `GOOGLE` vs `DDGS_FALLBACK`.
- **Freshness Level**: `LIVE` (<10m), `RECENT` (10m–1h), `STALE` (>1h).
- **Source Link**: Real merchant URL (`https://www.amazon.in/...`, `https://www.flipkart.com/...`).
