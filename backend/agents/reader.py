"""Reader agent — extracts structured facts from raw source snippets.

Activated only for deep or comparative questions.
"""

from __future__ import annotations

from langsmith import traceable

from backend.llm import call_llm

Source = dict[str, str]


@traceable(name="reader_agent", run_type="chain")
def reader_agent(question: str, sources: list[Source]) -> list[str]:
    """Read source snippets and extract 5-10 key facts relevant to the question."""
    snippets = "\n\n".join(
        f"[{i + 1}] {s['title']}\n{s['snippet']}"
        for i, s in enumerate(sources[:8])
    )
    prompt = f"""Read these source snippets and extract 5-10 key facts relevant to the question.
Return ONLY the facts, one per line, no numbering.

Question: {question}

Sources:
{snippets}"""
    text = call_llm(prompt, max_tokens=600)
    return [line.strip() for line in text.splitlines() if line.strip()]
