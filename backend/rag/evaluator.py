"""Ragas-based evaluation for generated answers."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from .llm import complete
from .scorecard import score_async


def build_reference(question: str, contexts: list[str]) -> str:
    joined = "\n\n".join(contexts[:3]) or "No context available."
    prompt = f"""Answer the question using only the retrieved context.
Be concise, factual, and do not add unsupported claims.

Question: {question}

Retrieved context:
{joined}"""
    return complete(prompt, max_tokens=350)


def evaluate_answer(question: str, answer: str, contexts: list[str], reference: str) -> dict[str, float | str]:
    if not answer.strip() or not contexts:
        return {"note": "RAG evaluation skipped because no retrieved context was available."}
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        scores = asyncio.run(score_async(question, answer, contexts, reference))
    else:
        with ThreadPoolExecutor(max_workers=1) as pool:
            scores = pool.submit(
                lambda: asyncio.run(score_async(question, answer, contexts, reference))
            ).result()
    scores["note"] = "Heuristic Ragas scores, not ground truth."
    return scores
