# HELIOS — Tavily Price Verification & Freshness Semantics

## Search Price vs Direct Page Verified
1. **Search Snippet Price (`SEARCH_PRICE`)**:
   - Initial candidate discovery parses structured INR price signals from Tavily search snippets.
   - Status marked as `SEARCH_PRICE`.

2. **Direct Page Verification (`DIRECT_PAGE_VERIFIED`)**:
   - Before human authorization or payment execution, `ProductVerifier` directly inspects top candidate merchant web pages.
   - Upon successful live verification of product page content, status upgrades to `DIRECT_PAGE_VERIFIED`.

## Price Freshness Categories
- **LIVE**: Retrieved within < 10 minutes.
- **RECENT**: Retrieved within 10 minutes – 1 hour.
- **STALE**: Retrieved > 1 hour ago.

## EMI & Subscription Rejection Rules
The regex parser explicitly rejects monthly or EMI pricing patterns:
- `₹99/month`
- `Rs. 149/mo`
- `₹199 per month`
Only total item purchase prices are accepted as valid product prices.
