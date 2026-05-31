"""global_search.py

Multi-stage hybrid RAG retrieval using LlamaIndex primitives end-to-end.

Pipeline:  rephrase  →  multi-query  →  HyDE  →  vector+BM25  →  RRF+dedup  →  LLM rerank
"""

import json
from llama_index.core import VectorStoreIndex
from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.core.indices.query.schema import QueryBundle
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.schema import TextNode
from llama_index.retrievers.bm25 import BM25Retriever

from .indexer import GLOBAL_STORAGE_DIR, get_global_storage
from .llm import get_llama_embed_model, get_llama_llm


def search_global_db(query: str, top_k: int = 3, num_variants: int = 5) -> dict:
    print(f"\n=== Searching global database for: '{query}' ===")
    llm = get_llama_llm()
    storage = get_global_storage()

    # 1. REPHRASE — clean grammar, expand abbreviations, keep intent
    rephrased = str(llm.complete(
        f"Rephrase clearly, keep intent. Return only the question:\n{query}"
    )).strip()
    print(f"  → Rephrased: {rephrased}")

    # 2. HyDE — vector search uses a hypothetical answer, not the raw query
    hyde = HyDEQueryTransform(llm=llm, include_original=True)

    # Load vector + BM25 retrievers
    vector_retriever = VectorStoreIndex.from_vector_store(
        storage.vector_store, embed_model=get_llama_embed_model()
    ).as_retriever(similarity_top_k=top_k * 2)

    raw_chunks = json.loads((GLOBAL_STORAGE_DIR / "bm25_index.json").read_text("utf-8"))
    if not raw_chunks:
        return {"error": "Global database is empty."}
    nodes = [TextNode(id_=c["id"], text=c["text"], metadata=c["metadata"]) for c in raw_chunks]
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=top_k * 2)
    print(f"  → Loaded {len(raw_chunks)} chunks")

    # 3 + 4 + 5. MULTI-QUERY + HYBRID RETRIEVAL + RRF + DEDUP
    # QueryFusionRetriever does all four in one primitive:
    #   - num_queries generates K paraphrases via the LLM
    #   - it runs every variant against every child retriever
    #   - "reciprocal_rerank" fuses all ranked lists with RRF
    #   - dedup happens automatically by node_id
    fusion = QueryFusionRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        llm=llm,
        num_queries=num_variants + 1,   # +1 keeps the original
        mode="reciprocal_rerank",
        similarity_top_k=top_k * 4,
        use_async=False,
    )
    candidates = fusion.retrieve(hyde.run(QueryBundle(query_str=rephrased)))
    print(f"  → {len(candidates)} unique candidates after fusion + dedup")

    # 6. LLM RERANK — final precision pass
    best = LLMRerank(llm=llm, choice_batch_size=5, top_n=top_k).postprocess_nodes(
        candidates, QueryBundle(query_str=rephrased)
    )
    print(f"  → Returning {len(best)} reranked chunks")

    results = [
        {"text": n.node.text, "score": n.score,
         "source": n.node.metadata.get("source_file", "Unknown")}
        for n in best
    ]
    return {
        "query": query,
        "rephrased_query": rephrased,
        "results": results,
        "joined_text": "\n".join(r["text"] for r in results),
    }