"""DuckDuckGo search — wrapped as a LangChain tool.

The Searcher agent calls `search_web()`.  If you ever want to swap in
Tavily, SerpAPI, or Brave Search, change only this file.
"""

from __future__ import annotations

from langsmith import traceable

from langchain_community.tools import DuckDuckGoSearchResults


_search_tool = DuckDuckGoSearchResults(
    output_format="list",
    num_results=3,
)


@traceable(name="search_web", run_type="tool")
def search_web(query: str) -> list[dict]:
    """Run a single search query and return a list of result dicts.

    Each dict has keys: 'snippet', 'title', 'link'.
    """
    try:
        results = _search_tool.invoke(query)
        # DuckDuckGoSearchResults returns list[dict] when output_format="list"
        if isinstance(results, list):
            return results
        return []
    except Exception:
        return []
