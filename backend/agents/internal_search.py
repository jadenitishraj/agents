"""Internal Search Agent — uses the global RAG v2 database."""

from __future__ import annotations

from langsmith import traceable

from backend.rag_v2.pipeline import search_rag
from backend.rag_v2.llm import complete

@traceable(name="internal_search_agent", run_type="chain")
def internal_search_agent(question: str) -> dict:
    """Search the global vector/graph/BM25 database and extract facts."""
    print("    Internal Search -> Querying global DB...")
    
    # We hit the Global DB using the new rag_v2 pipeline
    search_result = search_rag(question, top_k=5)
    
    contexts = [item["text"] for item in search_result.get("results", [])]
    
    if not contexts:
        return {"facts": [], "contexts": []}
        
    joined = "\n\n".join(contexts[:5])
    prompt = f"""Extract 3 to 5 concise facts that answer the question using ONLY the provided context.
Return one fact per line with no numbering.

Question: {question}

Context:
{joined}"""
    
    text = complete(prompt, max_tokens=500)
    facts = [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
    
    return {
        "facts": facts,
        "contexts": contexts,
    }
