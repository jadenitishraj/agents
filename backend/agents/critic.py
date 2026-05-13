"""Critic agent — reviews the draft answer and approves or rejects it.

The Critic is the quality gate.  It checks source count, word count,
and asks the LLM whether the answer actually addresses the question.
"""

from __future__ import annotations

from langsmith import traceable

from backend.llm import call_llm

Source = dict[str, str]


@traceable(name="critic_agent", run_type="chain")
def critic_agent(
    question: str,
    answer: str,
    sources: list[Source],
) -> tuple[bool, list[str]]:
    """Review the answer and return (approved, issues)."""
    issues: list[str] = []

    if len(sources) < 3:
        issues.append(f"Too few sources ({len(sources)} found, need at least 3)")

    word_count = len(answer.split())
    if word_count < 100:
        issues.append(f"Answer too brief ({word_count} words, need at least 100)")

    prompt = f"""Does this answer fully address the question?
Reply with EXACTLY one of:
  APPROVE
  REJECT: <one short reason>

Question: {question}

Answer: {answer}"""
    verdict = call_llm(prompt, max_tokens=80)
    if verdict.upper().startswith("REJECT"):
        reason = verdict.split(":", 1)[1].strip() if ":" in verdict else "Incomplete"
        issues.append(f"Aspect check failed: {reason}")

    return len(issues) == 0, issues
