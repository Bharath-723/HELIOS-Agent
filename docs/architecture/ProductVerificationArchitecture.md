# HELIOS — Product Verification Architecture

## Search Price vs Direct Page Verified Price

HELIOS enforces a strict boundary between unverified search snippets and direct product page verification:

1. **SEARCH_PRICE**: Initial price extracted from Google/DDGS search snippets (`verification_status = "SEARCH_PRICE"`).
2. **DIRECT_PAGE_VERIFIED**: Direct HTTP verification of candidate store URL confirming live price and in-stock status (`verification_status = "DIRECT_PAGE_VERIFIED"`).
3. **UNVERIFIED**: Candidate store page could not be accessed directly (`verification_status = "UNVERIFIED"`).

## Verification Module (`core/commerce/product_verifier.py`)

`ProductVerifier.verify_candidate_url()` attempts direct HTTP retrieval of candidate store URLs while respecting rate limits, robots.txt, and HTTP status codes.
