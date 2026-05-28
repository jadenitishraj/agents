import os
import sys
import asyncio
import httpx
from pathlib import Path

# Adjust path so we can import from backend
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from backend.rag.evaluator import evaluate_answer, build_reference
from backend.rag.llm import configure_settings, get_llama_llm

async def run_pipeline_test():
    print("=== Starting RAG End-to-End Pipeline & Ragas Evaluation Test ===")

    # 1. Setup API configuration
    configure_settings()

    # 2. Upload test document to FastAPI
    test_doc_path = Path(__file__).resolve().parent / "test_doc.txt"
    if not test_doc_path.exists():
        print(f"Error: {test_doc_path} does not exist.")
        return

    print(f"\n1. Uploading test document '{test_doc_path.name}' to FastAPI...")
    async with httpx.AsyncClient() as client:
        with open(test_doc_path, "rb") as f:
            files = {"file": (test_doc_path.name, f, "text/plain")}
            response = await client.post("http://localhost:8000/rag/upload", files=files, timeout=60.0)

        if response.status_code != 200:
            print(f"Upload failed: {response.text}")
            return

        upload_data = response.json()
        corpus_id = upload_data["corpus_id"]
        print(f"✓ Upload successful! Corpus ID: {corpus_id}, Chunks: {upload_data['chunks']}")

        # 3. Search document using pure retrieval
        query = "When was NovaTech Solutions founded and who are the founders?"
        print(f"\n2. Searching corpus '{corpus_id}' with query: '{query}'...")
        search_payload = {
            "query": query,
            "corpus_id": corpus_id,
            "top_k": 3
        }
        response = await client.post("http://localhost:8000/rag/search", json=search_payload, timeout=60.0)

        if response.status_code != 200:
            print(f"Search failed: {response.text}")
            return

        search_data = response.json()
        results = search_data["results"]
        print(f"✓ Search successful! Retrieved {len(results)} chunks in {search_data['elapsed_seconds']}s")

        for idx, res in enumerate(results):
            print(f"\n--- Chunk {idx + 1} (Score: {res['score']}) ---")
            print(res["text"][:200] + "...")

        # 4. Generate answer and reference using LLM for Ragas evaluation
        print("\n3. Generating answer and reference using LLM context...")
        contexts = [res["text"] for res in results]
        
        # Ground truth reference
        reference = "NovaTech Solutions was founded in March 2019 by Priya Sharma and Arjun Mehta."
        
        # Heuristic answer generated using context
        answer = build_reference(query, contexts)
        print(f"Generated Answer: {answer}")
        print(f"Ground Truth Reference: {reference}")

        # 5. Run Ragas Evaluation Scorecard
        print("\n4. Running Ragas Evaluation scorecard...")
        scores = evaluate_answer(query, answer, contexts, reference)
        
        print("\n=== Ragas Scorecard Results ===")
        for metric, score in scores.items():
            if metric != "note":
                print(f"- {metric.replace('_', ' ').title()}: {score}")
            else:
                print(f"Note: {score}")

if __name__ == "__main__":
    asyncio.run(run_pipeline_test())
