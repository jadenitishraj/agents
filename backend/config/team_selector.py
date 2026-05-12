"""Team selector — decides which roles from the taxonomy are needed for a question.

Taxonomy = the full catalog.  Team selection = the active subset for one run.
"""

from __future__ import annotations

from backend.config.taxonomy import TAXONOMY, DEEP_KEYWORDS, SENSITIVE_KEYWORDS


def needs_deep_reading(question: str) -> bool:
    """Return True if the question looks deep or comparative."""
    lowered = question.lower()
    if len(question.split()) > 15:
        return True
    return any(kw in lowered for kw in DEEP_KEYWORDS)


def is_sensitive(question: str) -> bool:
    """Return True if the question touches a sensitive domain."""
    lowered = question.lower()
    return any(kw in lowered for kw in SENSITIVE_KEYWORDS)


def select_team(question: str) -> list[str]:
    """Select the active team of agents for this question.

    Always-on roles are included unconditionally.
    Optional roles are added based on question analysis.
    """
    team = [role for role, info in TAXONOMY.items() if info["always"]]

    if needs_deep_reading(question):
        team.append("Reader")

    if is_sensitive(question):
        team.append("Compliance")

    return team
