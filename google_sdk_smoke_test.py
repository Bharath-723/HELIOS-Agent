"""
google_sdk_smoke_test.py — Isolated Smoke Test for google-genai SDK
====================================================================
Verifies python interpreter, google-genai SDK imports, client initialization,
credential masking, model discovery, and search grounding tool configuration.
"""

import os
import sys
import logging

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv(".env")

def run_smoke_test():
    print("=" * 60)
    print("HELIOS — Google SDK Smoke Test")
    print("=" * 60)

    # 1. Interpreter check
    print(f"1. PYTHON INTERPRETER:       {sys.executable}")

    # 2. SDK Import check
    try:
        from google import genai
        from google.genai import types
        print(f"2. GOOGLE-GENAI SDK:        PASS ({genai.__file__})")
    except Exception as e:
        print(f"2. GOOGLE-GENAI SDK:        FAIL ({e})")
        sys.exit(1)

    # 3. Credential check
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_CLOUD_API_KEY")
    masked_key = f"{key[:4]}...{key[-4:]}" if key and len(key) >= 8 else ("CONFIGURED" if key else "MISSING")
    print(f"3. CREDENTIAL STATUS:        {'CONFIGURED (' + masked_key + ')' if key else 'MISSING'}")

    if not key:
        print("   ❌ Key missing. Aborting smoke test.")
        sys.exit(1)

    # 4. Client initialization
    try:
        client = genai.Client(api_key=key)
        print("4. CLIENT INITIALIZATION:    PASS")
    except Exception as e:
        print(f"4. CLIENT INITIALIZATION:    FAIL ({e})")
        sys.exit(1)

    # 5. Search Grounding Tool Construction
    try:
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
        print("5. SEARCH GROUNDING TOOL:    AVAILABLE")
    except Exception as e:
        print(f"5. SEARCH GROUNDING TOOL:    FAIL ({e})")

    # 6. Model Discovery & Live API Check
    print("\n6. DISCOVERED MODELS & GROUNDING STATUS:")
    models_to_test = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-3.7-flash"]
    quota_exhausted = False
    model_found = None

    for m_name in models_to_test:
        try:
            resp = client.models.generate_content(
                model=m_name,
                contents="Search Google for wireless keyboard under 2000 INR price India",
                config=config
            )
            print(f"   • Model '{m_name}': SUCCESS")
            model_found = m_name
            break
        except Exception as exc:
            exc_str = str(exc)
            if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str or "quota" in exc_str.lower():
                quota_exhausted = True
                print(f"   • Model '{m_name}': 429 RESOURCE_EXHAUSTED (Quota limit reached)")
            elif "404" in exc_str or "NOT_FOUND" in exc_str:
                print(f"   • Model '{m_name}': 404 NOT_FOUND (Model unavailable)")
            else:
                print(f"   • Model '{m_name}': EXCEPTION ({type(exc).__name__}: {exc_str[:80]})")

    print("-" * 60)
    if model_found:
        print(f"RESULT: GOOGLE SDK PASS | MODEL {model_found} GROUNDING OK")
    elif quota_exhausted:
        print("RESULT: GOOGLE SDK PASS | SEARCH GROUNDING: BLOCKED_BY_QUOTA")
    else:
        print("RESULT: GOOGLE SDK PASS | SEARCH GROUNDING: FAILED")
    print("=" * 60)

if __name__ == "__main__":
    run_smoke_test()
