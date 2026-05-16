"""Planner agent — breaks one big question into smaller search tasks.

Pure function: question in, list of queries out.
"""

from __future__ import annotations

from langsmith import traceable
from langsmith.anonymizer import create_anonymizer
import re

from backend.llm import call_llm

pii_anonymizer = create_anonymizer([
    {"pattern": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'), "replace": "[EMAIL REDACTED]"},
    {"pattern": re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'), "replace": "[PHONE REDACTED]"}
])

@traceable(name="planner_agent", run_type="chain", process_inputs=pii_anonymizer)
def planner_agent(question: str) -> list[str]:
    """Break a research question into 3-5 specific web search queries."""
    prompt = f"""Break this research question into 3 to 5 specific web search queries.
Return ONLY the queries, one per line, no numbering or extra text.

Question: {question}"""
    text = call_llm(prompt, max_tokens=200, agent_name="Planner")
    queries = [line.strip() for line in text.splitlines() if line.strip()]
    return queries[:5]
