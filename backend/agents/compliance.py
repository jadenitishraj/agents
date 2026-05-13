"""Compliance agent — adds guardrails for sensitive domains.

Produces a disclaimer that the Writer should include when the topic
touches medical, legal, financial, or similar high-stakes areas.
"""

from __future__ import annotations

from langsmith import traceable

from backend.llm import call_llm


@traceable(name="compliance_agent", run_type="chain")
def compliance_agent(question: str) -> str:
    """Generate a one-sentence disclaimer for a sensitive-domain question."""
    prompt = f"""This question is in a sensitive domain (medical/legal/financial).
Write ONE sentence disclaimer the answer should include.

Question: {question}"""
    return call_llm(prompt, max_tokens=100)
