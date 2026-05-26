"""Citation extraction from retrieved nodes."""

from __future__ import annotations

from .models import Source


def contexts_and_citations(reranked: list) -> tuple[list[str], list[Source]]:
    contexts: list[str] = []
    citations: list[Source] = []
    seen_urls: set[str] = set()
    for item in reranked:
        node = item.node
        content = node.get_content()
        contexts.append(content)
        url = node.metadata.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            citations.append(
                {
                    "title": node.metadata.get("title", "Retrieved Context"),
                    "url": url,
                    "snippet": content[:240],
                }
            )
    return contexts, citations

