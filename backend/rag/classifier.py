"""Source classification and parser routing."""

from __future__ import annotations

import re

from .models import ClassifiedSource, Source


def _detect_kind(text: str) -> tuple[str, str]:
    lowered = text.lower()
    if "<html" in lowered or "<div" in lowered:
        return "html_page", "html"
    if "# " in text or "## " in text or "- " in text:
        return "markdown_notes", "markdown"
    if re.search(r"\b\d{1,2}:\d{2}\b", text) or "speaker" in lowered:
        return "transcript", "semantic"
    if re.search(r"\b(error|warn|trace|stack|http)\b", lowered):
        return "unstructured_logs", "token"
    if len(text.splitlines()) > 8 and len(text.split()) > 180:
        return "reference_report", "hierarchical"
    return "clean_text", "sentence"


def classify_sources(sources: list[Source]) -> list[ClassifiedSource]:
    classified: list[ClassifiedSource] = []
    for source in sources:
        title = source.get("title", "").strip() or "Untitled Source"
        snippet = source.get("snippet", "").strip()
        text = source.get("content", "").strip() or f"{title}\n\n{snippet}"
        category, chunk_strategy = _detect_kind(text)
        metadata = {
            "title": title,
            "url": source.get("url", ""),
            "category": category,
            "chunk_strategy": chunk_strategy,
            "source_type": source.get("source_type", "web_search"),
        }
        classified.append(
            ClassifiedSource(title, source.get("url", ""), text, category, chunk_strategy, metadata)
        )
    return classified

