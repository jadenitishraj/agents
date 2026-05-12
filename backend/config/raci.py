"""RACI matrix — who does what, who owns it.

R = Responsible (does the work)
A = Accountable (owns the quality)
C = Consulted  (input was used)
I = Informed   (needs to know)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RACIEntry:
    """One row of the RACI matrix."""

    task: str
    responsible: str
    accountable: str
    consulted: str = ""
    informed: str = "Team"


def build_raci(team: list[str]) -> list[RACIEntry]:
    """Build the RACI matrix for the active team."""
    entries: list[RACIEntry] = []

    if "Planner" in team:
        entries.append(
            RACIEntry(task="Plan sub-queries", responsible="Planner", accountable="Critic")
        )
    if "Searcher" in team:
        entries.append(
            RACIEntry(
                task="Find sources",
                responsible="Searcher",
                accountable="Critic",
                consulted="Planner",
            )
        )
    if "Reader" in team:
        entries.append(
            RACIEntry(
                task="Extract facts",
                responsible="Reader",
                accountable="Critic",
                consulted="Searcher",
            )
        )
    if "Compliance" in team:
        entries.append(
            RACIEntry(
                task="Add disclaimer",
                responsible="Compliance",
                accountable="Critic",
            )
        )
    if "Writer" in team:
        entries.append(
            RACIEntry(
                task="Write answer",
                responsible="Writer",
                accountable="Critic",
                consulted="Searcher",
            )
        )
    if "Critic" in team:
        entries.append(
            RACIEntry(task="Verify answer", responsible="-", accountable="Critic")
        )

    return entries
