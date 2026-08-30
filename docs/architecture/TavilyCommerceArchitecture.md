# HELIOS — Tavily Commerce Search Subsystem Architecture

## Overview
HELIOS integrates Tavily Search API (`tavily-python`) as its **PRIMARY** real-time web research engine for agentic commerce operations.

```
                  +--------------------------------+
                  |         USER INTENT            |
                  +--------------------------------+
                                  |
                                  v
                  +--------------------------------+
                  |   Commerce Intent Detection    |
                  +--------------------------------+
                                  |
                                  v
                  +--------------------------------+
                  |    CommerceResearchAdapter     |
                  +--------------------------------+
                                  |
            +---------------------+---------------------+
            | (COMMERCE_SEARCH_PROVIDER = "tavily")      |
            v                                           v
+-----------------------+                   +-----------------------+
|  TavilySearchProvider | [PRIMARY]         |  GoogleSearchProvider | [OPTIONAL]
| (tavily-python SDK)   |                   | (google-genai SDK)    |
+-----------------------+                   +-----------------------+
            |                                           |
            | failure / zero results                    | failure / quota
            +---------------------+---------------------+
                                  |
                                  v
                     +--------------------------+
                     |    DDGSSearchProvider    | [FALLBACK]
                     |   (ddgs package >=8.0)   |
                     +--------------------------+
                                  |
                                  v
                     +--------------------------+
                     |    ProductCandidates     |
                     +--------------------------+
```

## Key Architectural Principles
1. **Primary Tavily Search Engine**: `TavilySearchProvider` operates as the primary research provider.
2. **Provider Hierarchy**:
   - `COMMERCE_SEARCH_PROVIDER=tavily`: Tavily -> DDGS.
   - `COMMERCE_SEARCH_PROVIDER=auto`: Tavily -> Google -> DDGS.
   - `COMMERCE_SEARCH_PROVIDER=google`: Google -> DDGS.
   - `COMMERCE_SEARCH_PROVIDER=ddgs`: DDGS.
3. **Controlled Fallback**: When primary Tavily search returns zero results or network failure, controlled fallback to `DDGSSearchProvider` activates automatically.
4. **Google Search Optionality**: `GoogleSearchProvider` remains fully isolated in the codebase with `GOOGLE_SEARCH_ENABLED=false` by default.
