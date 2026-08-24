"""
google_search_diagnostic.py — Direct Diagnostic Tool for Google Search Provider
================================================================================
Diagnoses exact failure causes in GoogleSearchProvider without invoking DDGS fallback.
"""

import os
import sys
import time
import logging

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("google_search_diagnostic")

from core.system import environment_manager
from core.commerce.search import GoogleSearchProvider, SearchResponse


def run_diagnostic():
    print("=" * 70)
    print("HELIOS — Google Search Provider Diagnostic")
    print("=" * 70)

    # 1. Environment & Key Inspection
    g_key = os.getenv("GOOGLE_API_KEY")
    gem_key = os.getenv("GEMINI_API_KEY")
    enabled = os.getenv("GOOGLE_SEARCH_ENABLED", "true")
    region = os.getenv("GOOGLE_SEARCH_REGION", "IN")
    lang = os.getenv("GOOGLE_SEARCH_LANGUAGE", "en")
    cx = os.getenv("GOOGLE_SEARCH_CX", "").strip()

    print("\n1. ENVIRONMENT CONFIGURATION:")
    print(f"  • GOOGLE_API_KEY Configured:  {'YES' if g_key and len(g_key.strip()) > 5 else 'NO'}")
    print(f"  • GEMINI_API_KEY Configured:  {'YES' if gem_key and len(gem_key.strip()) > 5 else 'NO'}")
    print(f"  • GOOGLE_SEARCH_ENABLED:      {enabled}")
    print(f"  • GOOGLE_SEARCH_REGION:       {region}")
    print(f"  • GOOGLE_SEARCH_LANGUAGE:     {lang}")
    print(f"  • GOOGLE_SEARCH_CX:           {'CONFIGURED' if cx and cx not in ('not_set', 'search_engine_cx') else 'UNCONFIGURED'}")

    # 2. SDK Availability Check
    print("\n2. GOOGLE-GENAI SDK CHECK:")
    sdk_ok = False
    try:
        from google import genai
        from google.genai import types
        print(f"  • SDK Status:                 AVAILABLE ({genai.__file__})")
        sdk_ok = True
    except Exception as e:
        print(f"  • SDK Status:                 UNAVAILABLE ({e})")

    # 3. Provider Availability Check
    provider = GoogleSearchProvider()
    print("\n3. PROVIDER INSTANTIATION:")
    print(f"  • Provider Available:         {provider.is_available()}")

    # 4. Direct Search Grounding Test
    active_key = provider.api_key
    if active_key and sdk_ok:
        print("\n4. DIRECT GEMINI SEARCH GROUNDING TEST:")
        try:
            client = genai.Client(api_key=active_key)
            config = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
            print("  • Tool Declaration:           VALID (types.Tool(google_search=types.GoogleSearch()))")
            
            models_to_test = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-3.7-flash"]
            for m_name in models_to_test:
                try:
                    resp = client.models.generate_content(
                        model=m_name,
                        contents="Search Google for wireless keyboard under 2000 INR price India",
                        config=config
                    )
                    print(f"  ✓ Model '{m_name}': SUCCESS! Response length: {len(resp.text or '')}")
                    if resp.candidates and resp.candidates[0].grounding_metadata:
                        gm = resp.candidates[0].grounding_metadata
                        chunks = getattr(gm, 'grounding_chunks', []) or []
                        print(f"  ✓ Grounding Chunks Count:     {len(chunks)}")
                    break
                except Exception as m_exc:
                    exc_str = str(m_exc)
                    if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str:
                        print(f"  ! Model '{m_name}': 429 RESOURCE_EXHAUSTED (Quota Limit)")
                    elif "404" in exc_str or "NOT_FOUND" in exc_str:
                        print(f"  ! Model '{m_name}': 404 NOT_FOUND")
                    else:
                        print(f"  ! Model '{m_name}': {type(m_exc).__name__}: {exc_str[:100]}")

        except Exception as gen_exc:
            print(f"  ❌ Direct Grounding Test Exception: {gen_exc}")

    # 5. Direct Custom Search REST Test
    if active_key:
        print("\n5. DIRECT CUSTOM SEARCH REST API TEST:")
        if not cx or cx in ("not_set", "search_engine_cx"):
            print("  • Custom Search Status:       SKIPPED (GOOGLE_SEARCH_CX not configured)")
        else:
            try:
                import requests
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": active_key,
                    "cx": cx,
                    "q": "wireless keyboard under 2000 India",
                    "num": 3,
                    "gl": "in"
                }
                res = requests.get(url, params=params, timeout=4.0)
                print(f"  • Custom Search REST Status Code: {res.status_code}")
                if res.status_code == 200:
                    items = res.json().get("items", [])
                    print(f"  ✓ Custom Search returned {len(items)} items.")
                else:
                    print(f"  ❌ Custom Search Error Payload: {res.text[:200]}")
            except Exception as e2:
                print(f"  ❌ Custom Search REST Exception: {e2}")

    # 6. Full Provider Search Execution Method Call
    print("\n6. EXECUTING GoogleSearchProvider.search() METHOD:")
    test_query = "wireless keyboard under 2000 India"
    t0 = time.time()
    resp: SearchResponse = provider.search(test_query)
    t1 = time.time()

    print(f"  • Success:                    {resp.success}")
    print(f"  • Provider Used:              {resp.provider_used}")
    print(f"  • Execution Time:             {(t1-t0)*1000:.1f} ms")
    print(f"  • Result Count:               {len(resp.results)}")
    print(f"  • Error Code:                 {resp.error_code or 'None'}")
    print(f"  • Error Message:              {resp.error_message or 'None'}")
    print(f"  • Fallback Allowed:           {resp.fallback_allowed}")

    if resp.results:
        print("  • Discovered Results:")
        for r in resp.results:
            print(f"     - {r.title} | {r.domain} | {r.url}")

    print("=" * 70)


if __name__ == "__main__":
    run_diagnostic()
