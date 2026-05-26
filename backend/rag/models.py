from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

Source = dict[str, str]


@dataclass
class ClassifiedSource:
    title: str
    url: str
    text: str
    category: str
    chunk_strategy: str
    metadata: dict[str, str]


@dataclass
class StorageBundle:
    persist_dir: Path
    collection_name: str
    graph_backend: str
    storage_context: Any
    vector_store: Any
    graph_store: Any


@dataclass
class IndexedCorpus:
    question: str
    sources: list[Source]
    classified: list[ClassifiedSource]
    documents: list[Any]
    nodes: list[Any]
    storage: StorageBundle
    vector_index: Any
    graph_index: Any | None = None


@dataclass
class RagReadResult:
    facts: list[str]
    contexts: list[str]
    citations: list[Source]
    parser_summary: dict[str, int]
    reference: str
    notes: list[str] = field(default_factory=list)
