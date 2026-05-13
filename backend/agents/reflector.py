"""Reflector agent — converts raw critic feedback into generalized lessons.

This is the Reflexion pattern (Shinn et al., 2023).  Instead of overwriting
feedback each iteration, the reflector produces a structured lesson that
gets *appended* to episodic memory.
"""

from __future__ import annotations

from dataclasses import dataclass

from langsmith import traceable


@dataclass
class Reflection:
    """One structured lesson learned from a past Critic rejection.

    - what_failed: a short description of the specific failure.
    - lesson_learned: the generalized rule the agent should follow next time.
    """

    iteration: int
    what_failed: str
    lesson_learned: str


@traceable(name="reflector_agent", run_type="chain")
def reflector_agent(
    question: str,
    draft: str,
    critic_issues: list[str],
    iteration: int,
) -> Reflection:
    """Convert raw Critic issues into a structured, generalized lesson.

    The abstraction step (specific failure → general rule) is the core of
    Reflexion.  A weak reflector will produce excuses instead of lessons —
    that is the rationalization failure mode.
    """
    what_failed = "; ".join(critic_issues)

    # Deterministic generalization rules for teaching purposes.
    # In production this would be an LLM call with a careful prompt.
    lesson_parts: list[str] = []
    joined = what_failed.lower()
    if "citation" in joined or "source" in joined:
        lesson_parts.append("Always cite at least one source per factual claim.")
    if "vague" in joined or "specific" in joined:
        lesson_parts.append("Prefer concrete numbers and named examples over generalities.")
    if "incomplete" in joined or "missing" in joined:
        lesson_parts.append("Address every part of the question, not just the easy parts.")
    if not lesson_parts:
        lesson_parts.append("Treat critic feedback as a constraint, not a suggestion.")

    return Reflection(
        iteration=iteration,
        what_failed=what_failed,
        lesson_learned=" ".join(lesson_parts),
    )
