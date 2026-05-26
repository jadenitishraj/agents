"""Adaptive chunking for classified sources."""

from __future__ import annotations

from llama_index.core import Document
from llama_index.core.node_parser import (
    HTMLNodeParser,
    HierarchicalNodeParser,
    MarkdownNodeParser,
    SemanticSplitterNodeParser,
    SentenceSplitter,
    TokenTextSplitter,
)

from .models import ClassifiedSource
from .llm import get_llama_embed_model


def _build_parser(strategy: str):
    if strategy == "markdown":
        return MarkdownNodeParser()
    if strategy == "html":
        return HTMLNodeParser()
    if strategy == "semantic":
        return SemanticSplitterNodeParser(
            embed_model=get_llama_embed_model(),
            breakpoint_percentile_threshold=90,
        )
    if strategy == "hierarchical":
        return HierarchicalNodeParser.from_defaults(chunk_sizes=[1536, 768, 256])
    if strategy == "token":
        return TokenTextSplitter(chunk_size=512, chunk_overlap=50)
    return SentenceSplitter(chunk_size=768, chunk_overlap=80)


def parse_sources(items: list[ClassifiedSource]) -> tuple[list[Document], list]:
    documents: list[Document] = []
    nodes: list = []
    for item in items:
        document = Document(text=item.text, metadata=item.metadata)
        parser = _build_parser(item.chunk_strategy)
        parsed = parser.get_nodes_from_documents([document])
        for node in parsed:
            node.metadata.update(item.metadata)
        documents.append(document)
        nodes.extend(parsed)
    return documents, nodes
