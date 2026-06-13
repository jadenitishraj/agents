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
    internal_contexts: list[str] = None,
) -> tuple[bool, list[str]]:
    """Review the answer and return (approved, issues)."""
    
    from backend.config.team_selector import is_simple_question, is_arithmetic, is_notion
    
    if is_simple_question(question) or is_arithmetic(question) or is_notion(question):
        # Simple, arithmetic, and Notion queries are auto-approved.
        return True, []
        
    issues: list[str] = []
    
    if internal_contexts and len(internal_contexts) > 0:
        # If we have internal chunks, we bypass rejection rules and trust the RAG context.
        return True, []
    else:
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
    verdict = call_llm(prompt, max_tokens=80, agent_name="Critic")
    if verdict.upper().startswith("REJECT"):
        reason = verdict.split(":", 1)[1].strip() if ":" in verdict else "Incomplete"
        issues.append(f"Aspect check failed: {reason}")

    return len(issues) == 0, issues
