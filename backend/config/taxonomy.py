"""Taxonomy — the catalog of roles in the system.

Each role has:
- mission:  what it does (one sentence).
- always:   True if it is always on the team, False if conditional.
- phase:    "pipeline" (runs once in sequence) or "loop" (part of the writer-critic loop).
- order:    execution order within its phase.

The dynamic graph builder in orchestrator.py reads phase and order
to wire only the roles that are on the team.
"""

from __future__ import annotations

TAXONOMY: dict[str, dict] = {
    "Planner": {
        "mission": "Break the question into smaller search queries.",
        "always": True,
        "phase": "pipeline",
        "order": 1,
    },
    "Searcher": {
        "mission": "Find sources on the web using DuckDuckGo.",
        "always": True,
        "phase": "pipeline",
        "order": 2,
    },
    "InternalSearcher": {
        "mission": "Search the internal global RAG database.",
        "always": True,
        "phase": "pipeline",
        "order": 3,
    },
    "Reader": {
        "mission": "Read source snippets and extract structured facts.",
        "always": False,
        "phase": "pipeline",
        "order": 4,
    },
    "Compliance": {
        "mission": "Add guardrails for sensitive domains.",
        "always": False,
        "phase": "pipeline",
        "order": 5,
    },
    "Writer": {
        "mission": "Synthesize findings into a clear answer.",
        "always": True,
        "phase": "loop",
        "order": 1,
    },
    "Critic": {
        "mission": "Review the answer and approve or reject it.",
        "always": True,
        "phase": "loop",
        "order": 2,
    },
}

# Keywords used by team_selector.py to decide which optional roles to activate.

DEEP_KEYWORDS: list[str] = [
    "compare",
    "vs",
    "versus",
    "difference",
    "analyze",
    "explain how",
    "tradeoff",
    "trade-off",
    "evaluate",
]

SENSITIVE_KEYWORDS: list[str] = [
    "medical",
    "diagnosis",
    "treatment",
    "drug",
    "disease",
    "legal",
    "law",
    "lawsuit",
    "tax",
    "investment",
    "financial advice",
    "loan",
    "mortgage",
]
