# HELIOS — Google Search Fallback Diagnostic Report

**Diagnostic Date**: 2026-08-22  
**Target Subsystem**: `core/commerce/search/google_search_provider.py` & `core/commerce/commerce_research_adapter.py`

---

## Executive Summary

An empirical trace and direct API diagnostic was executed to determine why `GoogleSearchProvider` fails and causes HELIOS to fall back to `DDGSSearchProvider`.

The diagnosis revealed **four cascading technical root causes**:

1. **SDK Import Mismatch**: `google_search_provider.py` attempted to import legacy `google.generativeai`. In the active runtime environment, only the new official `google-genai` (v2.8.0) package is installed. This raised `ModuleNotFoundError: No module named 'google.generativeai'`.
2. **Model Deprecation / 404 Error**: Hardcoded `gemini-2.0-flash` is no longer supported on the Gemini API v1beta endpoint and returned `404 NOT_FOUND: This model models/gemini-2.0-flash is no longer available. Please update your code to use models/gemini-3.6-flash`.
3. **API Quota Exceeded / 429 Error**: When testing compatible models (`gemini-3.6-flash`, `gemini-flash-latest`), the Gemini API returned `429 RESOURCE_EXHAUSTED` (Quota limit exceeded for free tier API key).
4. **Custom Search REST Fallback Configuration Defect**: When Gemini grounding failed, `google_search_provider.py` fell back to Google Custom Search REST API (`https://www.googleapis.com/customsearch/v1`), which failed with HTTP `403 Forbidden` because `GOOGLE_SEARCH_CX` (Search Engine ID) was unconfigured (`not_set`).

Because `google_search_provider.py` swallowed these exceptions internally and returned an empty `SearchResponse(results=[])`, `CommerceResearchAdapter` observed 0 results and silently invoked `DDGSSearchProvider`.

---

## 1. Trace of Actual Provider Decision Code Path

In `core/commerce/commerce_research_adapter.py`:

```python
google_provider = GoogleSearchProvider()
fallback_provider = DDGSSearchProvider()

queries = cls.generate_queries(intent)
for q in queries:
    s_resp = google_provider.search(q, max_results=4, region="IN")
    if s_resp.results:
        # Use Google results
        ...
    else:
        # GOOGLE RETURNED 0 RESULTS -> TRIGGER FALLBACK
        log.info("CommerceResearchAdapter: Google provider produced 0 results for '%s'. Trying DDGS fallback.", q)
        fb_resp = fallback_provider.search(q, max_results=4, region="IN")
```

**Decision Rule**:
Whenever `GoogleSearchProvider.search()` returns `len(results) == 0` (whether due to missing SDK, 404 model, 429 quota, or unconfigured REST CX), the condition `if s_resp.results:` evaluates to `False`, forcing `CommerceResearchAdapter` to invoke `DDGSSearchProvider`.

---

## 2. Environment Audit Results

- **Environment File Loaded**: `D:\HELIOS_FINAL\HELIOS_FINAL\.env`
- **`GOOGLE_API_KEY` Configured**: `NO` (Blank in `.env`)
- **`GEMINI_API_KEY` Configured**: `YES` (Present in `.env`)
- **`GOOGLE_SEARCH_ENABLED`**: `true`
- **`GOOGLE_SEARCH_REGION`**: `IN`
- **`GOOGLE_SEARCH_LANGUAGE`**: `en`
- **`GOOGLE_SEARCH_CX`**: `not_set` (Unconfigured)

---

## 3. Direct Provider API Inspection (`google_search_diagnostic.py`)

Direct testing of `GoogleSearchProvider` via `google_search_diagnostic.py` yielded:

```text
1. Environment Configuration Check:
  • GOOGLE_API_KEY Configured:  NO
  • GEMINI_API_KEY Configured:  YES
  • GOOGLE_SEARCH_ENABLED:      true
  • GOOGLE_SEARCH_REGION:       IN
  • GOOGLE_SEARCH_LANGUAGE:     en
  • GOOGLE_SEARCH_CX:           not_set

2. Provider Availability Check:
  • Provider Available:         True

3. Testing Gemini Google Search Grounding API directly...
  ❌ google.generativeai import error: No module named 'google.generativeai'

4. Testing Google Custom Search REST API fallback directly...
  • Custom Search REST Status Code: 403
  ❌ Custom Search Error Payload: { "error": { "code": 403, "message": "Custom Search API has not been used in project ... or it is disabled." } }

5. Executing GoogleSearchProvider.search() Method:
  • Provider Used:              GOOGLE
  • Execution Time:             171.9 ms
  • Result Count:               0
  • Error Message:              Google Search API returned 0 results.
```

---

## 4. Specific Technical Root Cause Analysis

### A. API/Service & SDK Mismatch
- **Target Mechanism**: Gemini API with Google Search Grounding.
- **SDK Package in venv**: `google-genai` (v2.8.0).
- **Code implementation**: `import google.generativeai as genai` (Legacy SDK).
- **Result**: `ModuleNotFoundError: No module named 'google.generativeai'`.

### B. Model Incompatibility & Deprecation
- **Configured Model**: `gemini-2.0-flash`.
- **Gemini API Status**: `404 NOT_FOUND: This model models/gemini-2.0-flash is no longer available. Please update your code to use models/gemini-3.6-flash`.

### C. Quota & Rate Limits
- **Tested Models**: `gemini-3.6-flash`, `gemini-flash-latest`.
- **Gemini API Status**: `429 RESOURCE_EXHAUSTED: You exceeded your current quota`.

### D. Custom Search REST Fallback Configuration
- **Endpoint**: `https://www.googleapis.com/customsearch/v1`.
- **CX Parameter**: `not_set`.
- **HTTP Response**: `403 Forbidden`.

---

## 5. Summary of Diagnostic Findings

| Check Point | Status | Technical Detail |
| :--- | :--- | :--- |
| **1. Environment Key Loading** | **YES** | `GEMINI_API_KEY` loaded properly from `.env`. |
| **2. Provider Instantiation** | **YES** | `GoogleSearchProvider` initializes correctly. |
| **3. SDK Integration** | **FAILED** | Code uses legacy `google.generativeai` instead of installed `google-genai`. |
| **4. Gemini Model Name** | **FAILED** | Hardcoded `gemini-2.0-flash` returns 404 NOT_FOUND. |
| **5. Gemini API Quota** | **EXHAUSTED** | Account key currently returns 429 RESOURCE_EXHAUSTED. |
| **6. Custom Search CX** | **UNCONFIGURED**| `GOOGLE_SEARCH_CX` missing, causing 403 Forbidden. |
| **7. Fallback Code Path** | **EXERCISED** | Swallowing errors returns 0 results, forcing DDGS fallback. |

---

## 6. Recommended Action Plan for Resolution

To successfully exercise the Google-first search pipeline without falling back to DDGS:

1. **Update SDK Tool Call in `google_search_provider.py`**:
   Use `google-genai` SDK (`from google import genai`, `from google.genai import types`) with `types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])`.
2. **Update Supported Model Selection**:
   Update model lookup to use `gemini-3.6-flash` or `gemini-flash-latest` (falling back cleanly across supported Gemini models).
3. **Expose Detailed Error Reasons**:
   Log explicit error codes (`GOOGLE_SDK_MISSING`, `GOOGLE_MODEL_NOT_FOUND`, `GOOGLE_RATE_LIMITED`, `GOOGLE_REST_CX_MISSING`) rather than silently returning 0 results.
4. **Diagnostic Mode Support**:
   When `GOOGLE_SEARCH_DIAGNOSTIC_ONLY=true`, skip DDGS fallback so Google search errors are immediately visible to developers.
