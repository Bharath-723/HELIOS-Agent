"""HELIOS - Web Search: DuckDuckGo + AI summarization"""
import os

MAX = int(os.getenv("MAX_SEARCH_RESULTS", 5))

class WebSearch:
    def __init__(self, llm):
        self.llm = llm

    def search(self, query: str) -> str:
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            with DDGS() as d:
                results = list(d.text(query, max_results=MAX))
        except Exception as e:
            return f"Search failed: {e}"
        if not results:
            return f"No results found for '{query}'."
        raw = "\n\n".join(
            f"{i+1}. {r.get('title','')}\n{r.get('body','')[:300]}\n{r.get('href','')}"
            for i, r in enumerate(results))
        resp = self.llm.chat(
            prompt=f"Based on these results for '{query}', give a concise answer:\n\n{raw}",
            system="You are a research assistant. Summarize web results accurately and concisely.")
        return (f"Search: {query}\n\n{resp.content}\n\n"
                f"Sources:\n" + "\n".join(f"  • {r.get('href','')}" for r in results[:3]))
