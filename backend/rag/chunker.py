"""Chunker — split classified documents into search-ready chunks.

Why multiple strategies? Different documents need different splits.
A Markdown file has natural header-based sections. A transcript has
timestamps. A corporate PDF is dense prose. The classifier (parser.py)
picks the right strategy; this file executes it.

Strategies:
  markdown     → split on headers (# / ## / ###)
  html         → split on HTML tags (<div>, <section>)
  semantic     → split when the embedding similarity drops (topic change)
  hierarchical → multi-level split (1536 → 768 → 256 tokens)
  token        → fixed-size token windows (for logs, raw dumps)
  sentence     → default fallback — split on sentence boundaries
"""

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


def _build_splitter(strategy: str):
    """Return the right LlamaIndex node parser for the given strategy."""
    if strategy == "markdown":
        return MarkdownNodeParser()
    if strategy == "html":
        return HTMLNodeParser()
    if strategy == "semantic":
        # Semantic chunking: uses embedding similarity to detect topic shifts.
        # breakpoint_percentile_threshold=90 means: only split when similarity
        # drops below the 90th percentile — i.e., a significant topic change.
        return SemanticSplitterNodeParser(
            embed_model=get_llama_embed_model(),
            breakpoint_percentile_threshold=90,
        )
    if strategy == "hierarchical":
        # Multi-level chunks: coarse (1536) → medium (768) → fine (256).
        # Useful for long reference reports where both overview and detail matter.
        return HierarchicalNodeParser.from_defaults(chunk_sizes=[1536, 768, 256])
    if strategy == "token":
        # Fixed-size token windows — good for unstructured logs where there
        # are no natural sentence boundaries.
        return TokenTextSplitter(chunk_size=512, chunk_overlap=50)
    # Default: sentence-level splitting — works well for most clean text.
    return SentenceSplitter(chunk_size=768, chunk_overlap=80)


def chunk_sources(items: list[ClassifiedSource]) -> tuple[list[Document], list]:
    """Split classified sources into documents + nodes (chunks).

    Also enforces a safety guard: any chunk exceeding 20,000 characters
    (~5,000 tokens) gets sub-split to avoid hitting OpenAI's 8,192 token
    embedding limit.
    """
    print(f"Chunking {len(items)} classified sources...")
    documents: list[Document] = []
    nodes: list = []
    # Safety net: re-split oversized chunks that would blow the embedding API limit.
    fallback_splitter = SentenceSplitter(chunk_size=768, chunk_overlap=80)

    for item in items:
        print(f"  → Chunking '{item.title}' using {item.chunk_strategy} splitter...")
        document = Document(text=item.text, metadata=item.metadata)
        splitter = _build_splitter(item.chunk_strategy)
        parsed = splitter.get_nodes_from_documents([document])

        # Guard against oversized chunks from parsers that don't enforce limits
        # (e.g. MarkdownNodeParser on a doc with no headers → one giant chunk).
        safe_nodes = []
        for node in parsed:
            # 20,000 chars ≈ 5,000 tokens — safely below the 8,192 token API limit.
            if len(node.get_content()) > 20000:
                sub_docs = [Document(text=node.get_content(), metadata=node.metadata)]
                sub_nodes = fallback_splitter.get_nodes_from_documents(sub_docs)
                safe_nodes.extend(sub_nodes)
            else:
                safe_nodes.append(node)

        # Copy classification metadata onto every chunk so the retriever
        # can return source info (title, url, category) with each result.
        for node in safe_nodes:
            node.metadata.update(item.metadata)

        documents.append(document)
        nodes.extend(safe_nodes)
    print(f"  → Created {len(nodes)} chunks total.")
    return documents, nodes
