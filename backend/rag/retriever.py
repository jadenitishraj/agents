"""Retriever — search all 3 indexes, fuse results, and rerank.

The retriever answers the question "given a query, which chunks are
most relevant?" by querying three different indexes and merging:

1. Vector search  → semantic similarity from ChromaDB embeddings
2. BM25 search    → keyword matching using term frequency
3. Graph search   → entity hops from the knowledge graph

Then it fuses the results (reciprocal rank fusion) and reranks
with an LLM to produce the final top-k chunks.

Two public entry points:
  retrieve_context() — used by read_with_rag() in the agent pipeline
  search_corpus()    — used by /rag/search API (no answer generation)
"""

from __future__ import annotations

from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.retrievers import KGTableRetriever, QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever

from .llm import get_llama_llm
from .models import IndexedCorpus, Source

# ──────────────────────────────────────────────────────────────
# PRODUCTION NOTE: For a cost-free, faster reranker, swap
# LLMRerank with a local BERT cross-encoder:
#
#   pip install sentence-transformers
#
#   from llama_index.core.postprocessor import SentenceTransformerRerank
#   reranker = SentenceTransformerRerank(
#       model="cross-encoder/ms-marco-MiniLM-L-6-v2", top_n=top_k,
#   )
#
# Cross-encoders run locally on CPU, are free, faster (~50ms vs ~2s),
# and more accurate for relevance scoring since they were specifically
# trained for that task.
# ──────────────────────────────────────────────────────────────


# ─── HyDE query expansion ───────────────────────────────────
# HyDE (Hypothetical Document Embeddings) asks the LLM to generate
# a hypothetical answer to the question FIRST, then searches using
# that answer's embedding. This dramatically improves recall because
# the search embedding now "looks like" a real document chunk rather
# than a short question.

def _build_query_bundle(question: str):
    """Expand the question using HyDE for better semantic search."""
    transform = HyDEQueryTransform(llm=get_llama_llm(), include_original=True)
    return transform.run(question)


# ─── Graph search ────────────────────────────────────────────
# Queries the knowledge graph for entity-relationship hits.
# Returns empty list if no graph index was built.

def _graph_hits(corpus: IndexedCorpus, question: str) -> list:
    if corpus.graph_index is None:
        return []
    try:
        retriever = KGTableRetriever(corpus.graph_index, retriever_mode="keyword")
    except Exception:
        retriever = corpus.graph_index.as_retriever(retriever_mode="keyword")
    return list(retriever.retrieve(question))


# ─── Citation extraction ────────────────────────────────────
# Pulls source metadata (title, url, snippet) from reranked nodes
# and deduplicates by URL so the same source isn't cited twice.

def _contexts_and_citations(reranked: list) -> tuple[list[str], list[Source]]:
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
            citations.append({
                "title": node.metadata.get("title", "Retrieved Context"),
                "url": url,
                "snippet": content[:240],
            })
    return contexts, citations


# ─── Hybrid retrieval + rerank ───────────────────────────────
# Combines BM25 (keyword) + Vector (semantic) + Graph (entity) results
# using reciprocal rank fusion, then reranks with an LLM.
# This gives the best of all three worlds.

def retrieve_context(corpus: IndexedCorpus, question: str) -> tuple[list[str], list[Source]]:
    """Full retrieval pipeline used by the multi-agent reader path."""
    print(f"Retrieving context for query: '{question}'")
    print("  → Generating HyDE query expansion...")
    query_bundle = _build_query_bundle(question)

    # Build retrievers for keyword and semantic search.
    print("  → Searching Vector and BM25 indexes...")
    vector = corpus.vector_index.as_retriever(similarity_top_k=10)
    bm25 = BM25Retriever.from_defaults(nodes=corpus.nodes, similarity_top_k=10)

    # Reciprocal rank fusion: merge BM25 + vector results, generate 3
    # query variations for broader coverage, and take top 6.
    fusion = QueryFusionRetriever(
        [vector, bm25],
        llm=get_llama_llm(),
        num_queries=3,
        mode="reciprocal_rerank",
        similarity_top_k=6,
        use_async=False,
    )
    print("  → Searching Knowledge Graph & fusing results...")
    candidates = list(fusion.retrieve(query_bundle)) + _graph_hits(corpus, question)

    # Deduplicate by node ID (same chunk from different retrievers).
    unique: dict[str, object] = {}
    for item in candidates:
        unique[item.node.node_id] = item

    # LLM reranker: score each chunk by how well it answers the question.
    print("  → LLM reranking top candidates to find the best chunks...")
    reranker = LLMRerank(llm=get_llama_llm(), choice_batch_size=5, top_n=3)
    reranked = reranker.postprocess_nodes(list(unique.values()), query_bundle=query_bundle)
    return _contexts_and_citations(reranked)


# ─── Pure retrieval search (no answer generation) ────────────
# Used by the /rag/search API endpoint. Same pipeline as above
# but returns structured dicts with scores instead of raw text.

def search_corpus(
    corpus: IndexedCorpus,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """Return top-k chunks with scores and metadata. No LLM answer."""
    print(f"\n=== Executing Standalone RAG Search ===")
    print(f"Retrieving context for query: '{query}'")
    print("  → Generating HyDE query expansion...")
    query_bundle = _build_query_bundle(query)

    print("  → Searching Vector and BM25 indexes...")
    vector = corpus.vector_index.as_retriever(similarity_top_k=10)
    bm25 = BM25Retriever.from_defaults(nodes=corpus.nodes, similarity_top_k=10)

    fusion = QueryFusionRetriever(
        [vector, bm25],
        llm=get_llama_llm(),
        num_queries=3,
        mode="reciprocal_rerank",
        similarity_top_k=top_k + 5,
        use_async=False,
    )

    print("  → Fusing results (reciprocal rank)...")
    candidates = list(fusion.retrieve(query_bundle))
    unique: dict[str, object] = {}
    for item in candidates:
        unique[item.node.node_id] = item

    print("  → LLM reranking top candidates...")
    reranker = LLMRerank(llm=get_llama_llm(), choice_batch_size=5, top_n=top_k)
    reranked = reranker.postprocess_nodes(list(unique.values()), query_bundle=query_bundle)

    results: list[dict] = []
    for item in reranked:
        node = item.node
        results.append({
            "text": node.get_content(),
            "score": round(float(item.score), 4),
            "title": node.metadata.get("title", "Unknown"),
            "url": node.metadata.get("url", ""),
            "category": node.metadata.get("category", ""),
            "chunk_strategy": node.metadata.get("chunk_strategy", ""),
        })
    return results
