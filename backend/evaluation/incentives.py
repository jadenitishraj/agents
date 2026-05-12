"""Incentive scanner — detects behavioral drift risks after a run.

A system can be structurally correct and still behave badly if its
rewards point in the wrong direction.  This module looks at a finished
run and flags patterns that suggest drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.orchestrator import State


@dataclass
class IncentiveRisk:
    """One detected incentive risk."""

    name: str
    why: str
    mitigation: str


def scan_incentives(trace: dict) -> list[IncentiveRisk]:
    """Scan a finished trace for incentive risks.

    Checks: speed-over-depth, thin research, missing compliance, rubber-stamping.
    """
    risks: list[IncentiveRisk] = []

    if trace.get("iterations", 0) == 1 and len(trace.get("answer", "").split()) < 200:
        risks.append(
            IncentiveRisk(
                name="Speed over depth",
                why="Approved on first iteration with a short answer.",
                mitigation="Reward iteration; require a depth check before approval.",
            )
        )

    if trace.get("sources_count", 0) < 3:
        risks.append(
            IncentiveRisk(
                name="Thin research",
                why=f"Only {trace.get('sources_count', 0)} source(s) — risk of low-evidence answer.",
                mitigation="Set a minimum-sources threshold; require more diverse queries.",
            )
        )

    if trace.get("was_sensitive", False) and "Compliance" not in trace.get("team", []):
        risks.append(
            IncentiveRisk(
                name="Missing Compliance role",
                why="Sensitive topic detected but Compliance was not on the team.",
                mitigation="Tighten sensitivity detection; make Compliance harder to skip.",
            )
        )

    if trace.get("critic_first_pass", False) and trace.get("iterations", 0) == 1:
        risks.append(
            IncentiveRisk(
                name="Critic rubber-stamped",
                why="Approved on first try — could indicate weak gates.",
                mitigation="Add stricter Critic checks; reward thoroughness over speed.",
            )
        )

    return risks
