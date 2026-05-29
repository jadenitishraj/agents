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
