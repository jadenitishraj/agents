"""Pure retrieval search — no answer generation.

Uses HyDE query expansion, BM25+Vector fusion, and LLM reranker.
Returns raw chunks with scores and citations.

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
# This runs locally on CPU, is free, faster (~50ms vs ~2s),
# and is more accurate for relevance scoring since cross-encoders
# are specifically trained for that task.
# ──────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from llama_index.core.postprocessor import LLMRerank
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever

from .llm import get_llama_llm
from .models import IndexedCorpus
from .query_transform import build_query_bundle


def search_corpus(
    corpus: IndexedCorpus,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """Return top-k chunks with scores and metadata. No LLM answer."""
    query_bundle = build_query_bundle(query)

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

    candidates = list(fusion.retrieve(query_bundle))
    unique: dict[str, object] = {}
    for item in candidates:
        unique[item.node.node_id] = item

    # Using LLMRerank here — see module docstring for the
    # production cross-encoder alternative.
    reranker = LLMRerank(
        llm=get_llama_llm(), choice_batch_size=5, top_n=top_k,
    )
    reranked = reranker.postprocess_nodes(
        list(unique.values()), query_bundle=query_bundle,
    )

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
