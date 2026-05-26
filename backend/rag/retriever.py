"""Hybrid retrieval, graph lookup, and reranking."""

from __future__ import annotations

from llama_index.core.postprocessor import LLMRerank
from llama_index.core.retrievers import KGTableRetriever, QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever

from .citations import contexts_and_citations
from .models import IndexedCorpus, Source
from .query_transform import build_query_bundle
from .llm import get_llama_llm


def _graph_hits(corpus: IndexedCorpus, question: str) -> list:
    if corpus.graph_index is None:
        return []
    try:
        retriever = KGTableRetriever(corpus.graph_index, retriever_mode="keyword")
    except Exception:
        retriever = corpus.graph_index.as_retriever(retriever_mode="keyword")
    return list(retriever.retrieve(question))


def retrieve_context(corpus: IndexedCorpus, question: str) -> tuple[list[str], list[Source]]:
    query_bundle = build_query_bundle(question)
    vector = corpus.vector_index.as_retriever(similarity_top_k=10)
    bm25 = BM25Retriever.from_defaults(nodes=corpus.nodes, similarity_top_k=10)
    fusion = QueryFusionRetriever(
        [vector, bm25],
        llm=get_llama_llm(),
        num_queries=3,
        mode="reciprocal_rerank",
        similarity_top_k=6,
        use_async=False,
    )
    candidates = list(fusion.retrieve(query_bundle)) + _graph_hits(corpus, question)
    unique: dict[str, object] = {}
    for item in candidates:
        unique[item.node.node_id] = item
    reranker = LLMRerank(llm=get_llama_llm(), choice_batch_size=5, top_n=3)
    reranked = reranker.postprocess_nodes(list(unique.values()), query_bundle=query_bundle)
    return contexts_and_citations(reranked)
