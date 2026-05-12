"""Searcher agent — gathers external evidence using the search tool.

Uses the DuckDuckGo tool from tools/search.py.  The agent decides
what to search; the tool does the actual retrieval.
"""

from __future__ import annotations

from backend.tools.search import search_web

Source = dict[str, str]


def searcher_agent(queries: list[str]) -> list[Source]:
    """Search the web for each query and return deduplicated sources.

    Each source is a dict with keys: title, url, snippet.
    """
    sources: list[Source] = []
    seen_urls: set[str] = set()

    for query in queries:
        results = search_web(query)
        for result in results:
            url = result.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append(
                    {
                        "title": result.get("title", ""),
                        "url": url,
                        "snippet": result.get("snippet", ""),
                    }
                )

    return sources
