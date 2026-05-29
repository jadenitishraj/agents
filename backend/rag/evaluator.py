"""Evaluator — score RAG retrieval quality using Ragas metrics.

Ragas is an LLM-as-a-judge framework that scores retrieval quality
without needing human annotations. It evaluates four dimensions:

1. Faithfulness     — Did the answer only use facts from the retrieved context?
                      (Catches hallucination: making up facts not in the chunks.)

2. Answer Relevance — Does the answer actually address the user's question?
                      (Catches drift: answering a different question.)

3. Context Precision — Are the most relevant chunks ranked highest?
                      (Catches bad ordering: burying the answer in chunk #5.)

4. Context Recall   — Did we retrieve ALL the chunks needed to answer fully?
                      (Catches missed context: only finding 2 of 4 key facts.)
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from ragas import SingleTurnSample
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithoutReference,
    LLMContextRecall,
    ResponseRelevancy,
)

from .llm import complete, get_langchain_embeddings, get_langchain_llm


# ─── Ragas scorecard computation ─────────────────────────────
# Runs all 4 metrics asynchronously against a single question/answer pair.
# Each metric is an independent LLM judge call.

async def _score_async(
    question: str,
    answer: str,
    contexts: list[str],
    reference: str,
) -> dict[str, float]:
    llm = LangchainLLMWrapper(get_langchain_llm())
    embeds = LangchainEmbeddingsWrapper(get_langchain_embeddings())
    sample = SingleTurnSample(
        user_input=question,
        response=answer,
        retrieved_contexts=contexts,
        reference=reference,
    )
    metrics = {
        "faithfulness": Faithfulness(llm=llm),
        "answer_relevance": ResponseRelevancy(llm=llm, embeddings=embeds),
        "context_precision": LLMContextPrecisionWithoutReference(llm=llm),
        "context_recall": LLMContextRecall(llm=llm),
    }
    scores: dict[str, float] = {}
    for name, metric in metrics.items():
        scores[name] = round(float(await metric.single_turn_ascore(sample)), 4)
    return scores


# ─── Reference generation ───────────────────────────────────
# Generates a "gold standard" answer from the retrieved context
# so Ragas can compare the actual answer against it.

def build_reference(question: str, contexts: list[str]) -> str:
    joined = "\n\n".join(contexts[:3]) or "No context available."
    prompt = f"""Answer the question using only the retrieved context.
Be concise, factual, and do not add unsupported claims.

Question: {question}

Retrieved context:
{joined}"""
    return complete(prompt, max_tokens=350)


# ─── Public evaluation entry point ──────────────────────────
# Handles the async-to-sync bridge so callers don't need to
# worry about event loops (works both inside and outside FastAPI).

def evaluate_answer(question: str, answer: str, contexts: list[str], reference: str) -> dict[str, float | str]:
    if not answer.strip() or not contexts:
        return {"note": "RAG evaluation skipped because no retrieved context was available."}
    
    print("\n=== Starting Ragas Evaluation ===")
    print("  → Running LLM judges for Faithfulness, Relevance, Precision, and Recall...")

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No event loop running — safe to use asyncio.run().
        scores = asyncio.run(_score_async(question, answer, contexts, reference))
    else:
        # Already inside an event loop (e.g. FastAPI) — run in a thread.
        with ThreadPoolExecutor(max_workers=1) as pool:
            scores = pool.submit(
                lambda: asyncio.run(_score_async(question, answer, contexts, reference))
            ).result()
    scores["note"] = "Heuristic Ragas scores, not ground truth."
    return scores
