# HELIOS — Google-First Commerce Research Architecture

## Overview

HELIOS integrates Google Search as its primary web research engine for natural language agentic commerce. The architecture uses provider abstraction (`core/commerce/search/`) to query Google Search / Gemini Search Grounding first, falling back to DDGS if Google credentials are missing or unavailable.

## High-Level Execution Pipeline

```mermaid
flowchart TD
    UserQuery[User Prompt: 'Find wireless keyboard under ₹2000'] --> Intent[CommerceIntentClassifier]
    Intent -->|Research Intent| Adapter[CommerceResearchAdapter]
    
    Adapter --> GoogleProv[GoogleSearchProvider (PRIMARY)]
    GoogleProv -->|Success| Normalizer[Product Normalizer & Deduplication]
    GoogleProv -->|Failure / No Key| DDGSProv[DDGSSearchProvider (FALLBACK)]
    DDGSProv --> Normalizer
    
    Normalizer --> Verifier[ProductVerifier (Direct Page Check)]
    Verifier -->|SEARCH_PRICE / DIRECT_PAGE_VERIFIED| Recommender[CommerceRecommender]
    Recommender --> Cost[CommerceCalculator]
    
    Cost --> AuthGuard[CommerceAuthorizationGuard (Revalidate Price)]
    AuthGuard --> UI[Transaction Review Card]
    UI -->|Human Authorize Button| Razorpay[Razorpay Sandbox Execution]
```

## Core Provider Abstraction (`core/commerce/search/`)

- `base_search_provider.py`: `BaseSearchProvider` abstract interface.
- `google_search_provider.py`: Primary Google provider loading `GOOGLE_API_KEY` / `GEMINI_API_KEY` strictly from environment variables.
- `fallback_search_provider.py`: Fallback search provider identifying as `DDGS_FALLBACK`.
- `search_models.py`: Strongly typed `SearchResult` and `SearchResponse` models.
