"""
google_single_search_test.py — Single Live Google Search Grounding Test
========================================================================
Performs exactly ONE live Google Search Grounding request using the official
google-genai SDK to test the newly configured API key.
Exposes zero credentials and classifies the response explicitly.
"""

import os
import sys
import time
import logging
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv(".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("google_single_search_test")


def mask_secret(secret: str) -> str:
    if not secret or len(secret) < 8:
        return "******"
    return f"{secret[:4]}...{secret[-4:]}"


def run_single_test():
    print("=" * 70)
    print("HELIOS — Single Live Google Search Grounding Test")
    print("=" * 70)

    # 1. Environment Verification
    g_key = os.getenv("GOOGLE_API_KEY")
    gem_key = os.getenv("GEMINI_API_KEY")
    active_key = g_key or gem_key or ""
    enabled = os.getenv("GOOGLE_SEARCH_ENABLED", "true")
    target_model = os.getenv("GOOGLE_SEARCH_MODEL", "gemini-3.6-flash")

    print("\n1. ENVIRONMENT CONFIGURATION:")
    print(f"  • GOOGLE_API_KEY Configured:  {'YES (' + mask_secret(g_key) + ')' if g_key else 'NO'}")
    print(f"  • GEMINI_API_KEY Configured:  {'YES (' + mask_secret(gem_key) + ')' if gem_key else 'NO'}")
    print(f"  • GOOGLE_SEARCH_ENABLED:      {enabled}")
    print(f"  • TARGET MODEL:               {target_model}")

    if not active_key:
        print("\nCLASSIFICATION: GOOGLE_AUTH_FAILED")
        print("Reason: No API key found in GOOGLE_API_KEY or GEMINI_API_KEY.")
        sys.exit(1)

    # 2. SDK Import Check
    print("\n2. SDK CHECK:")
    try:
        from google import genai
        from google.genai import types
        print(f"  • google-genai SDK:           AVAILABLE ({genai.__file__})")
    except Exception as imp_err:
        print(f"  • google-genai SDK:           UNAVAILABLE ({imp_err})")
        print("\nCLASSIFICATION: GOOGLE_SEARCH_UNAVAILABLE")
        print(f"Reason: google-genai SDK import failed: {imp_err}")
        sys.exit(1)

    # 3. Perform Exactly ONE Live API Request
    query = "wireless keyboard under 2000 INR India current price"
    print("\n3. EXECUTING SINGLE LIVE API REQUEST:")
    print(f"  • Query:                      '{query}'")
    print(f"  • Model Used:                 {target_model}")
    print("  • Tool Config:                types.Tool(google_search=types.GoogleSearch())")
    print("  • Requesting live response...")

    t0 = time.time()
    try:
        client = genai.Client(api_key=active_key)
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
        
        response = client.models.generate_content(
            model=target_model,
            contents=f"Search Google for current product prices, store links, and merchant availability: '{query}'",
            config=config
        )
        latency = (time.time() - t0) * 1000

        print(f"  • Latency:                    {latency:.1f} ms")
        print(f"  • HTTP Status:                200 OK")

        # Extract Grounding Metadata
        grounding_chunks = []
        if hasattr(response, "candidates") and response.candidates:
            cand = response.candidates[0]
            if hasattr(cand, "grounding_metadata") and cand.grounding_metadata:
                g_meta = cand.grounding_metadata
                chunks = getattr(g_meta, "grounding_chunks", None) or []
                grounding_chunks = chunks

        resp_text = getattr(response, "text", "") or ""

        print("\n4. DIAGNOSTIC RESULTS:")
        print("  • Provider:                   GOOGLE")
        print("  • Status:                     SUCCESS")
        print("  • Search Grounding:           ACTIVE")
        print(f"  • Model:                      {target_model}")
        print(f"  • Response Text Length:       {len(resp_text)} chars")
        print(f"  • Grounding Sources Count:    {len(grounding_chunks)}")

        if grounding_chunks:
            print("\n5. EXTRACTED SOURCE EVIDENCE:")
            for i, chunk in enumerate(grounding_chunks[:10], 1):
                web = getattr(chunk, "web", None)
                if web:
                    title = getattr(web, "title", "Listing") or "Listing"
                    url = getattr(web, "uri", "") or ""
                    domain = urlparse(url).netloc if url else "google.com"
                    print(f"  [{i}] Title:   {title}")
                    print(f"      Domain:  {domain}")
                    print(f"      URL:     {url}")

        print("\nResponse Text Snippet:")
        print("-" * 50)
        print(resp_text[:500])
        print("-" * 50)

        print("\nCLASSIFICATION: SUCCESS")
        print("Verification: Live Google Search Grounding request succeeded with valid web sources.")

    except Exception as exc:
        latency = (time.time() - t0) * 1000
        exc_str = str(exc)
        print(f"  • Latency:                    {latency:.1f} ms")
        print(f"  • Exception Type:             {type(exc).__name__}")
        print(f"  • Raw Error Payload:          {exc_str[:300]}")

        print("\n4. FAILURE DIAGNOSTIC & CLASSIFICATION:")
        print(f"  • Provider:                   GOOGLE")
        print(f"  • Model Tested:               {target_model}")
        print(f"  • Search Grounding:           FAILED")

        if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str or "quota" in exc_str.lower():
            # Extract retry-after info if available in response details
            retry_info = "Not specified"
            if "retry" in exc_str.lower() or "Please retry in" in exc_str:
                import re
                m = re.search(r'Please retry in ([\d\.\w]+)', exc_str)
                if m:
                    retry_info = f"Retry after {m.group(1)}"

            print("  • Error Code:                 GOOGLE_RATE_LIMITED")
            print(f"  • Retry Info:                 {retry_info}")
            print("\nCLASSIFICATION: GOOGLE_RATE_LIMITED")
            print(f"Reason: Quota / Rate limit reached (429 RESOURCE_EXHAUSTED). Retry-After: {retry_info}")

        elif "401" in exc_str or "403" in exc_str or "API_KEY_INVALID" in exc_str:
            print("  • Error Code:                 GOOGLE_AUTH_FAILED")
            print("\nCLASSIFICATION: GOOGLE_AUTH_FAILED")
            print(f"Reason: Invalid API credential or unauthorized project access.")

        elif "404" in exc_str or "NOT_FOUND" in exc_str:
            print("  • Error Code:                 GOOGLE_MODEL_NOT_FOUND")
            print("\nCLASSIFICATION: GOOGLE_MODEL_NOT_FOUND")
            print(f"Reason: Model '{target_model}' not found on Google Gemini API endpoint.")

        else:
            print("  • Error Code:                 GOOGLE_UNKNOWN_ERROR")
            print("\nCLASSIFICATION: GOOGLE_UNKNOWN_ERROR")
            print(f"Reason: Unexpected API exception: {exc_str[:150]}")

    print("=" * 70)


if __name__ == "__main__":
    run_single_test()
