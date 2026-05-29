import json
from pathlib import Path

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.indices.query.schema import QueryBundle
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.schema import TextNode
from llama_index.core.postprocessor import LLMRerank

from .indexer import get_global_storage, GLOBAL_STORAGE_DIR
from .llm import get_llama_embed_model, get_llama_llm

def search_global_db(query: str, top_k: int = 3) -> dict:
    """Independent retrieval function that queries all global DBs."""
    print(f"\n=== Searching global database for: '{query}' ===")
    storage = get_global_storage()
    
    # 1. Load Vector Index
    try:
        vector_index = VectorStoreIndex.from_vector_store(
            storage.vector_store, embed_model=get_llama_embed_model()
        )
        vector_retriever = vector_index.as_retriever(similarity_top_k=top_k * 2)
    except Exception as e:
        print(f"Error loading vector DB: {e}")
        return {"error": "Vector database is empty or corrupted. Upload a file first."}
        
    # 2. Load BM25 Index from the dedicated file
    bm25_path = GLOBAL_STORAGE_DIR / "bm25_index.json"
    if not bm25_path.exists():
        return {"error": "BM25 file not found. Upload a file first."}
        
    with open(bm25_path, "r", encoding="utf-8") as f:
        raw_chunks = json.load(f)
        
    if not raw_chunks:
        return {"error": "Global database is empty."}
        
    print(f"  → Loaded {len(raw_chunks)} total chunks from bm25_index.json")
    nodes = [TextNode(id_=c["id"], text=c["text"], metadata=c["metadata"]) for c in raw_chunks]
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=top_k * 2)
    
    # 3. Hybrid Fusion (Vector + BM25)
    print("  → Fusing Vector and BM25 results...")
    fusion = QueryFusionRetriever([vector_retriever, bm25_retriever], mode="reciprocal_rerank")
    
    query_bundle = QueryBundle(query_str=query)
    candidates = fusion.retrieve(query_bundle)
    
    # 4. LLM Reranking
    print("  → LLM reranking top candidates to find the best chunks...")
    reranker = LLMRerank(llm=get_llama_llm(), choice_batch_size=5, top_n=top_k)
    best_nodes = reranker.postprocess_nodes(candidates, query_bundle)
    
    # Format the results into a simple Python dictionary
    results = []
    for node in best_nodes:
        results.append({
            "text": node.node.text,
            "score": node.score,
            "source": node.node.metadata.get("source_file", "Unknown")
        })
        
    print(f"  → Found {len(results)} relevant chunks!")
    return {
        "query": query, 
        "results": results
    }
