"""HELIOS - Web Search: DuckDuckGo + AI summarization"""
import os
import logging

log = logging.getLogger("helios.web_search")

MAX = int(os.getenv("MAX_SEARCH_RESULTS", 5))

class WebSearch:
    def __init__(self, llm):
        self.llm = llm

    def search(self, query: str) -> str:
        log.info("web_search called: query='%s'", query)
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            
            with DDGS() as d:
                results = list(d.text(query, max_results=MAX))
        except Exception as e:
            log.error("DuckDuckGo search failed: %s", e, exc_info=True)
            return f"Search failed: {e}"

        if not results:
            log.warning("No search results found for query: '%s'", query)
            return f"No results found for '{query}'."

        raw = "\n\n".join(
            f"{i+1}. {r.get('title','')}\n{r.get('body','')[:300]}\n{r.get('href','')}"
            for i, r in enumerate(results))

        log.info("Found %d search results, calling LLM for summarization...", len(results))
        try:
            resp = self.llm.chat(
                prompt=f"Based on these results for '{query}', give a concise answer:\n\n{raw}",
                system="You are a research assistant. Summarize web results accurately and concisely.")
            
            log.info("LLM summarization completed successfully.")
            return (f"Search: {query}\n\n{resp.content}\n\n"
                    f"Sources:\n" + "\n".join(f"  • {r.get('href','')}" for r in results[:3]))
        except Exception as exc:
            log.error("LLM summarization failed: %s", exc, exc_info=True)
            # Fallback to returning raw search results directly instead of failing the whole query
            fallback_sources = "\n".join(f"  • {r.get('title','')}: {r.get('href','')}" for r in results[:5])
            return (f"Search: {query}\n\n"
                    f"⚠ Summarization offline (LLM error). Showing raw search matches:\n\n{fallback_sources}")
