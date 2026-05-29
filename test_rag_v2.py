import asyncio
import os
from pathlib import Path
from backend.rag_v2.pipeline import ingest_file, search_rag
from backend.rag_v2.llm import get_llama_llm
from backend.rag_v2.ragas_evaluation import run_ragas_evaluation

def test_rag_v2():
    print("=== Testing RAG v2 Global Persistence ===")
    
    # 1. Create a dummy test file
    test_file = Path("test_document.txt")
    test_file.write_text(
        "Python is a high-level, interpreted programming language. "
        "It was created by Guido van Rossum and first released in 1991. "
        "Python's design philosophy emphasizes code readability with its notable use of significant indentation. "
        "Its language constructs and object-oriented approach aim to help programmers write clear, logical code for small and large-scale projects."
    )
    print(f"\n1. Created test file: {test_file}")
    
    # 2. Upload/Ingest the file (This should save to Vector, Graph, and BM25)
    print("\n2. Ingesting file into global database...")
    ingest_result = ingest_file(str(test_file))
    print(ingest_result)
    
    # 3. Search the global database
    question = "Who created the Python programming language and when was it released?"
    print(f"\n3. Searching for: '{question}'")
    search_results = search_rag(question, top_k=2)
    
    contexts = [res["text"] for res in search_results["results"]]
    
    if not contexts:
        print("❌ Search failed to find any contexts.")
        return
        
    for i, ctx in enumerate(contexts):
        print(f"  Context {i+1}: {ctx[:100]}...")
        
    # 4. Generate an answer using the retrieved context
    print("\n4. Generating Answer...")
    llm = get_llama_llm()
    prompt = f"""Answer the question using ONLY the provided context.
Question: {question}
Context: {' | '.join(contexts)}
Answer:"""
    
    response = llm.complete(prompt)
    answer = str(response)
    print(f"  Answer: {answer}")
    
    # 5. Evaluate with Ragas
    print("\n5. Running Ragas Evaluation...")
    scores = run_ragas_evaluation(question=question, answer=answer, contexts=contexts)
    
    print("\n=== Final Ragas Scores ===")
    for metric, score in scores.items():
        print(f"  - {metric.capitalize()}: {score}")
        
    # Cleanup dummy file
    if test_file.exists():
        test_file.unlink()

if __name__ == "__main__":
    test_rag_v2()
