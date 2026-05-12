"""Writer agent — synthesizes findings into a clear answer.

Accepts optional critic feedback (or Reflexion lessons) to improve rewrites.
"""

from __future__ import annotations

from backend.llm import call_llm

Source = dict[str, str]


def writer_agent(
    question: str,
    sources: list[Source],
    facts: list[str],
    disclaimer: str = "",
    critic_feedback: str = "",
) -> str:
    """Write a clear, well-structured answer (150-300 words) to the question."""
    sources_text = "\n".join(
        f"- {s['title']} ({s['url']})" for s in sources[:8]
    )
    facts_text = "\n".join(f"- {f}" for f in facts) if facts else "(none)"
    feedback_text = ""
    if critic_feedback:
        feedback_text = (
            "\n\nPREVIOUS CRITIC FEEDBACK TO ADDRESS:\n"
            f"{critic_feedback}"
        )

    disclaimer_line = (
        f"Include this disclaimer at the end: {disclaimer}" if disclaimer else ""
    )
    prompt = f"""Write a clear, well-structured answer (150-300 words) to the question.
Use the facts and cite sources where appropriate.
{disclaimer_line}

Question: {question}

Facts:
{facts_text}

Sources:
{sources_text}{feedback_text}"""
    return call_llm(prompt, max_tokens=600)
