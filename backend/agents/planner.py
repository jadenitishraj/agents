"""Planner agent — breaks one big question into smaller search tasks.

Pure function: question in, list of queries out.
"""

from __future__ import annotations

from langsmith import traceable

from backend.llm import call_llm


@traceable(name="planner_agent", run_type="chain")
def planner_agent(question: str) -> list[str]:
    """Break a research question into 3-5 specific web search queries."""
    prompt = f"""Break this research question into 3 to 5 specific web search queries.
Return ONLY the queries, one per line, no numbering or extra text.

Question: {question}"""
    text = call_llm(prompt, max_tokens=200)
    queries = [line.strip() for line in text.splitlines() if line.strip()]
    return queries[:5]
