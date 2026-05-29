import asyncio
from concurrent.futures import ThreadPoolExecutor

from ragas import SingleTurnSample
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithoutReference,
    ResponseRelevancy,
)

from .llm import get_langchain_embeddings, get_langchain_llm

async def _score_async(
    question: str,
    answer: str,
    contexts: list[str],
) -> dict[str, float]:
    llm = LangchainLLMWrapper(get_langchain_llm())
    embeds = LangchainEmbeddingsWrapper(get_langchain_embeddings())
    
    # SingleTurnSample doesn't strictly need a reference if we use WithoutReference metrics
    sample = SingleTurnSample(
        user_input=question,
        response=answer,
        retrieved_contexts=contexts,
    )
    
    metrics = {
        "faithfulness": Faithfulness(llm=llm),
        "answer_relevance": ResponseRelevancy(llm=llm, embeddings=embeds),
        "context_precision": LLMContextPrecisionWithoutReference(llm=llm),
    }
    
    scores: dict[str, float] = {}
    for name, metric in metrics.items():
        scores[name] = round(float(await metric.single_turn_ascore(sample)), 4)
    return scores


def run_ragas_evaluation(question: str, answer: str, contexts: list[str]) -> dict:
    if not answer.strip() or not contexts:
        return {"error": "Skipped because answer or context is empty"}
    
    print("\n=== Starting Ragas Evaluation ===")
    print("  → Running LLM judges for Faithfulness, Relevance, and Precision...")

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No event loop running
        scores = asyncio.run(_score_async(question, answer, contexts))
    else:
        # Inside an event loop
        with ThreadPoolExecutor(max_workers=1) as pool:
            scores = pool.submit(
                lambda: asyncio.run(_score_async(question, answer, contexts))
            ).result()
            
    print("  → Evaluation Complete!")
    return scores

if __name__ == "__main__":
    import json
    from dotenv import load_dotenv
    load_dotenv()
    
    from backend.rag_v2.pipeline import search_rag
    from backend.rag_v2.llm import complete
    
    print("==================================================")
    print("         RUNNING LIVE RAGAS INTEGRATION TEST      ")
    print("==================================================")
    
    # 1. Ask a question to search against the live database
    test_question = "Who carved the glass clocks of Veridia?"
    print(f"Querying global RAG DB for: '{test_question}'...")
    
    # 2. Trigger the live retriever
    search_result = search_rag(test_question, top_k=3)
    live_contexts = [r["text"] for r in search_result.get("results", [])]
    joined_text = search_result.get("joined_text", "")
    
    # 3. Fallback gracefully if database is completely empty
    if not live_contexts:
        print("\n[!] Global DB is empty (no files uploaded yet).")
        print("    → Falling back to dummy contexts for evaluation validation.")
        live_contexts = [
            "Legend says the glass clocks of Veridia, which never lose a single second, were hand-carved by the elusive chronomancer Elara using pure starlight.",
            "Veridia is a city known for its beautiful glasswork and ancient magical artifacts."
        ]
        joined_text = "\n".join(live_contexts)
        
    print(f"  → Retrieved {len(live_contexts)} chunk(s).")
    
    # 4. Generate a live LLM Answer based on the retrieved contexts
    print("Generating live answer from contexts...")
    generation_prompt = f"""Answer the question concisely using ONLY the provided context.
If the context does not contain the answer, say "I don't know".

Question: {test_question}

Context:
{joined_text}"""
    
    live_answer = complete(generation_prompt)
    print(f"  → Live Answer: '{live_answer}'")
    
    # 5. Run live Ragas evaluation
    result_scores = run_ragas_evaluation(test_question, live_answer, live_contexts)
    print("\n--- Final Live Ragas Scorecard ---")
    print(json.dumps(result_scores, indent=2))
    print("==================================================")
