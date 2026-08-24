"""
core/commerce/search/result_classifier.py — Search Result Classification & Quality Scoring
========================================================================================
Deterministically classifies web search results into PRODUCT_PAGE, MERCHANT_COLLECTION,
EDITORIAL, VIDEO, FORUM, GENERAL_WEB, or UNKNOWN. Calculates source evidence scores.
"""

import re
from urllib.parse import urlparse
from typing import Dict, Any, Tuple


class ResultClassifier:
    """Classifies web search results and computes deterministic evidence quality scores."""

    INDIAN_PREFERRED_MERCHANTS = [
        "amazon.in",
        "flipkart.com",
        "croma.com",
        "reliancedigital.in",
        "vijaysales.com",
        "tatacliq.com",
        "myntra.com",
        "redragon.in",
        "logitech.com",
        "dell.com",
        "hp.com",
        "lenovo.com",
        "elitehubs.com"
    ]

    EDITORIAL_DOMAINS = [
        "techradar.com", "91mobiles.com", "gadgets360.com",
        "digit.in", "mysmartprice.com", "computerserversolutions.com",
        "cashify.in", "medium.com"
    ]

    @classmethod
    def classify(cls, url: str, title: str = "", snippet: str = "") -> str:
        """Classifies a search result based on URL structure, domain, and content signals."""
        if not url:
            return "UNKNOWN"

        url_lower = url.lower()
        parsed = urlparse(url_lower)
        domain = parsed.netloc
        path = parsed.path
        query = parsed.query

        # 1. Video Classification
        if any(v in domain for v in ["youtube.com", "youtu.be", "vimeo.com", "dailymotion.com"]):
            return "VIDEO"

        # 2. Forum Classification
        if any(f in domain for f in ["reddit.com", "quora.com", "stackexchange.com"]) or "/forum/" in path or "/discussion/" in path:
            return "FORUM"

        # 3. Editorial / Blog / Review Article Classification
        if any(ed in domain for ed in cls.EDITORIAL_DOMAINS) or "/blog/" in path or "/blogs/" in path or "/article/" in path or "/news/" in path or "/guides/" in path or "top 10" in title.lower() or ("best " in title.lower() and "review" in title.lower()):
            return "EDITORIAL"

        # 4. Merchant Search Page (CRITICAL FIX)
        # Any URL containing search endpoints or query parameters like ?q= or /search is ALWAYS a search page, NEVER a direct product page
        if any(s_pat in path for s_pat in ["/search", "/find", "/query"]) or "q=" in query or "query=" in query or "keyword=" in query:
            return "MERCHANT_SEARCH_PAGE"

        # 5. Direct Product Page (Strict Signatures)
        if any(m in domain for m in cls.INDIAN_PREFERRED_MERCHANTS) or any(k in domain for k in ["store", "shop", "cart", "buy"]):
            # Direct Product Page signatures
            if any(sig in path for sig in ["/dp/", "/p/", "/product/", "/products/", "/pd/", "/item/", "/buy/"]) or re.search(r'/[a-z0-9\-]+-p-\d+', path) or re.search(r'/product-page/', path) or (re.search(r'/\d{5,}', path) and not any(c in path for c in ["/collections/", "/category/"])):
                return "DIRECT_PRODUCT_PAGE"

            # Merchant Category / Collection Page
            if any(sig in path for sig in ["/collections/", "/category/", "/categories/", "/catalog/", "/keyboards-under-"]):
                return "MERCHANT_COLLECTION"
            if "/c/" in path or "/department/" in path:
                return "CATEGORY_PAGE"

            # Default merchant page classification if no product ID signature is found
            return "MERCHANT_COLLECTION"

        # 6. Fallback Signatures for Generic Domains
        if any(sig in path for sig in ["/dp/", "/p/", "/product/", "/pd/", "/item/"]):
            return "DIRECT_PRODUCT_PAGE"
        if any(sig in path for sig in ["/collections/", "/category/", "/categories/"]):
            return "MERCHANT_COLLECTION"
        if "/search" in path or "q=" in query:
            return "MERCHANT_SEARCH_PAGE"

        return "GENERAL_WEB"

    @classmethod
    def calculate_evidence_score(
        cls,
        classification: str,
        domain: str,
        has_price_evidence: bool,
        search_confidence: float = 0.8
    ) -> float:
        """Calculates a deterministic evidence quality score (0.0 to 1.0)."""
        score = search_confidence * 0.5

        # Classification multiplier
        if classification in ("DIRECT_PRODUCT_PAGE", "PRODUCT_PAGE"):
            score += 0.35
        elif classification in ("MERCHANT_SEARCH_PAGE", "MERCHANT_COLLECTION", "CATEGORY_PAGE"):
            score += 0.15
        elif classification == "GENERAL_WEB":
            score += 0.10
        elif classification in ("EDITORIAL", "FORUM"):
            score += 0.05
        elif classification == "VIDEO":
            score += 0.02

        # Merchant domain bonus
        domain_lower = domain.lower()
        if any(m in domain_lower for m in cls.INDIAN_PREFERRED_MERCHANTS):
            score += 0.10

        # Price evidence bonus
        if has_price_evidence:
            score += 0.05

        return min(max(round(score, 2), 0.10), 1.0)
