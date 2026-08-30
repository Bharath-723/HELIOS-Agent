# HELIOS — Tavily Commerce Search Validation Test Results

## Test Suite: `tavily_search_validation.py`
- **Total Tests**: 20
- **Passed**: 20 (100% SUCCESS)
- **Execution Time**: 0.168s

## Test Coverage Matrix
1. `test_01_tavily_import`: **PASSED** (tavily-python imported)
2. `test_02_provider_initialization`: **PASSED** (TavilySearchProvider initialized)
3. `test_03_missing_api_key_handling`: **PASSED** (Returns `TAVILY_NOT_CONFIGURED`)
4. `test_04_api_key_detection_without_secret_leak`: **PASSED** (Secrets masked)
5. `test_05_search_configuration_defaults`: **PASSED** (Default settings verified)
6. `test_06_mocked_result_normalization`: **PASSED** (Normalizes Tavily JSON to SearchResult)
7. `test_07_source_url_preservation`: **PASSED** (Original URLs preserved)
8. `test_08_merchant_extraction`: **PASSED** (Extracts Amazon, Flipkart, Croma)
9. `test_09_price_extraction`: **PASSED** (Parses ₹1,749 INR correctly)
10. `test_10_emi_monthly_price_rejection`: **PASSED** (Rejects ₹149/mo)
11. `test_11_auth_error_classification`: **PASSED** (Returns `TAVILY_AUTH_FAILED`)
12. `test_12_rate_limit_classification`: **PASSED** (Returns `TAVILY_RATE_LIMITED`)
13. `test_13_provider_selection_hierarchy`: **PASSED** (`COMMERCE_SEARCH_PROVIDER=tavily`)
14. `test_14_tavily_to_ddgs_fallback`: **PASSED** (Fallback to DDGS on primary failure)
15. `test_15_google_search_optional`: **PASSED** (Google disabled by default)
16. `test_16_normal_hi_does_not_invoke_tavily`: **PASSED** (Conversational prompts skip search)
17. `test_17_commerce_request_invokes_tavily`: **PASSED** (Commerce intent triggers search)
18. `test_18_search_result_caching`: **PASSED** (Session cache prevents duplicate API calls)
19. `test_19_query_count_limit`: **PASSED** (Queries bounded to max 2 per request)
20. `test_20_secret_leakage_test`: **PASSED** (Secrets masked as `tvly...7890`)
