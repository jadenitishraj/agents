"""Public entrypoint for standalone RAG reading."""

from __future__ import annotations

from collections import Counter

from .evaluator import build_reference
from .indexer import build_corpus
from .models import RagReadResult, Source
from .retriever import retrieve_context
from .llm import complete


def _extract_facts(question: str, contexts: list[str]) -> list[str]:
    joined = "\n\n".join(contexts[:3]) or "No context."
    prompt = f"""Extract 5 to 8 concise facts that answer the question.
Return one fact per line with no numbering.

Question: {question}

Context:
{joined}"""
    text = complete(prompt, max_tokens=500)
    return [line.strip("- ").strip() for line in text.splitlines() if line.strip()]


def read_with_rag(question: str, sources: list[Source]) -> RagReadResult:
    if not sources:
        return RagReadResult([], [], [], {}, "", ["No sources available for RAG ingestion."])
    corpus = build_corpus(question, sources)
    contexts, citations = retrieve_context(corpus, question)
    facts = _extract_facts(question, contexts)
    summary = Counter(item.chunk_strategy for item in corpus.classified)
    reference = build_reference(question, contexts)
    return RagReadResult(facts, contexts, citations, dict(summary), reference)
