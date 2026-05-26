"""Async Ragas score calculation."""

from __future__ import annotations

from ragas import SingleTurnSample
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithoutReference,
    LLMContextRecall,
    ResponseRelevancy,
)

from .llm import get_langchain_embeddings, get_langchain_llm


async def score_async(
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

