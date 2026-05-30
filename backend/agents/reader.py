"""Reader agent — uses the standalone RAG package for deep reading."""

from __future__ import annotations

from langsmith import traceable

Source = dict[str, str]


@traceable(name="reader_agent", run_type="chain")
def reader_agent(question: str, sources: list[Source]) -> RagReadResult:
    """Read retrieved sources through the isolated RAG package."""
    return ""
