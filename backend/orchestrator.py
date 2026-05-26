"""Orchestrator — State, node wrappers, and dynamic graph builder.

This is the only file that imports LangGraph.  Agents are pure functions;
they don't know they live inside a graph.

The graph is built DYNAMICALLY from the team:
- If Reader isn't on the team, there is no Reader node in the graph.
- Pipeline-phase roles are wired in sequence by their `order`.
- Loop-phase roles (Writer, Critic) form the iterative rewrite loop.
- HITL (human_review) auto-approves after 3 seconds for sensitive questions.
"""

from __future__ import annotations

import time
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from backend.agents.planner import planner_agent
from backend.agents.searcher import searcher_agent
from backend.agents.reader import reader_agent
from backend.agents.writer import writer_agent
from backend.agents.critic import critic_agent
from backend.agents.compliance import compliance_agent
from backend.agents.reflector import reflector_agent, Reflection

from backend.config.taxonomy import TAXONOMY
from backend.config.team_selector import select_team, is_sensitive
from backend.config.raci import build_raci

# ---------------------------------------------------------------------------
# State — the data that flows through every node in the graph.
# ---------------------------------------------------------------------------

Source = dict[str, str]


class State(TypedDict, total=False):
    """The running state of a research pipeline."""

    # Input.
    question: str
    team: list[str]
    # Working data.
    queries: list[str]
    sources: list[Source]
    facts: list[str]
    rag_contexts: list[str]
    rag_citations: list[Source]
    rag_parser_summary: dict[str, int]
    rag_reference: str
    rag_metrics: dict
    disclaimer: str
    answer: str
    critic_feedback: str
    # Critic verdict.
    approved: bool
    issues: list[str]
    # Counters and metadata.
    iterations: int
    max_iterations: int
    sources_count: int
    llm_calls: int
    duration_seconds: float
    was_sensitive: bool
    critic_first_pass: bool
    final_answer: str
    # Reflexion — episodic memory of past failures.
    episodic_memory: list


# ---------------------------------------------------------------------------
# Node wrappers — thin adapters: State → agent function → dict update.
# ---------------------------------------------------------------------------

def planner_node(state: State) -> dict:
    """Run the Planner agent."""
    print("  Planner -> generating sub-queries...")
    queries = planner_agent(state["question"])
    print(f"    {len(queries)} queries generated")
    return {
        "queries": queries,
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def searcher_node(state: State) -> dict:
    """Run the Searcher agent and merge/dedup sources."""
    print("  Searcher -> searching DuckDuckGo...")
    new_sources = searcher_agent(state.get("queries", []))

    existing = state.get("sources", [])
    combined = existing + new_sources
    seen_urls: set[str] = set()
    deduped: list[Source] = []
    for source in combined:
        url = source.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(source)

    print(f"    {len(deduped)} unique sources collected")
    return {
        "sources": deduped,
        "sources_count": len(deduped),
    }


def reader_node(state: State) -> dict:
    """Run the Reader agent to extract facts."""
    print("  Reader -> extracting facts...")
    result = reader_agent(state["question"], state.get("sources", []))
    print(f"    {len(result.facts)} facts extracted from {len(result.contexts)} contexts")
    return {
        "facts": result.facts,
        "rag_contexts": result.contexts,
        "rag_citations": result.citations,
        "rag_parser_summary": result.parser_summary,
        "rag_reference": result.reference,
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def compliance_node(state: State) -> dict:
    """Run the Compliance agent (only once per run)."""
    if state.get("disclaimer"):
        return {}
    print("  Compliance -> generating disclaimer...")
    disclaimer = compliance_agent(state["question"])
    print("    Disclaimer ready")
    return {
        "disclaimer": disclaimer,
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def writer_node(state: State) -> dict:
    """Run the Writer agent with Reflexion-aware feedback."""
    print("  Writer -> synthesizing answer...")

    # Build feedback from episodic memory (Reflexion) if available.
    memory = state.get("episodic_memory", [])
    if memory:
        accumulated_lessons = "\n".join(
            f"- (iter {r.iteration}) {r.lesson_learned}" for r in memory
        )
        feedback = f"Lessons from previous attempts:\n{accumulated_lessons}"
    else:
        feedback = state.get("critic_feedback", "")

    answer = writer_agent(
        state["question"],
        state.get("sources", []),
        state.get("facts", []),
        state.get("disclaimer", ""),
        feedback,
    )
    iteration = state.get("iterations", 0) + 1
    print(f"    Draft ready ({len(answer.split())} words) — iteration {iteration}")
    return {
        "answer": answer,
        "iterations": iteration,
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def critic_node(state: State) -> dict:
    """Run the Critic agent with Reflexion — appends lessons to episodic memory."""
    print("  Critic -> reviewing...")
    approved, issues = critic_agent(
        state["question"],
        state.get("answer", ""),
        state.get("sources", []),
    )

    updates: dict = {
        "approved": approved,
        "issues": issues,
        "llm_calls": state.get("llm_calls", 0) + 1,
    }

    if approved:
        print("    APPROVED")
        if state.get("iterations", 0) == 1:
            updates["critic_first_pass"] = True
    else:
        print(f"    REJECTED: {'; '.join(issues)}")
        # Reflexion: append a generalized lesson instead of overwriting feedback.
        reflection = reflector_agent(
            state["question"],
            state.get("answer", ""),
            issues,
            state.get("iterations", 0),
        )
        memory = list(state.get("episodic_memory", []))
        memory.append(reflection)
        updates["episodic_memory"] = memory
        updates["critic_feedback"] = "; ".join(issues)

    return updates


def human_review_node(state: State) -> dict:
    """HITL gate — auto-approves after 3 seconds for sensitive questions.

    In a production system, this would pause and wait for a real human.
    Here we simulate the concept by logging the review and auto-approving.
    """
    if "Compliance" not in state.get("team", []):
        return {}
    if not state.get("approved", False):
        return {}

    print("  Human Review -> sensitive topic detected, review required...")
    print("    Draft under review...")
    time.sleep(3)
    print("    Auto-approved after 3 seconds")
    return {"approved": True}


# ---------------------------------------------------------------------------
# Node registry — maps role names to their node functions.
# ---------------------------------------------------------------------------

NODE_REGISTRY: dict[str, callable] = {
    "Planner": planner_node,
    "Searcher": searcher_node,
    "Reader": reader_node,
    "Compliance": compliance_node,
    "Writer": writer_node,
    "Critic": critic_node,
}


# ---------------------------------------------------------------------------
# Conditional edge routers.
# ---------------------------------------------------------------------------

MAX_ITERATIONS_DEFAULT = 3


def critic_router(state: State) -> str:
    """After the Critic, either loop back to Writer or finish."""
    if state.get("approved", True):
        return "human_review"
    if state.get("iterations", 0) >= state.get("max_iterations", MAX_ITERATIONS_DEFAULT):
        return "end"
    return "writer"


def human_router(state: State) -> str:
    """After the human review, either done or back to Writer."""
    if state.get("approved", False):
        return "end"
    if state.get("iterations", 0) >= state.get("max_iterations", MAX_ITERATIONS_DEFAULT):
        return "end"
    return "writer"


# ---------------------------------------------------------------------------
# Dynamic graph builder — wires only the nodes that are on the team.
# ---------------------------------------------------------------------------

def build_graph(team: list[str]) -> StateGraph:
    """Build a LangGraph StateGraph dynamically from the selected team.

    Pipeline-phase roles are wired in sequence by their `order`.
    Loop-phase roles form the iterative Writer → Critic loop.
    The human_review node is always present (it no-ops for non-sensitive runs).
    """
    graph = StateGraph(State)

    # Separate pipeline and loop roles, sorted by order.
    pipeline_roles = sorted(
        [r for r in team if TAXONOMY[r]["phase"] == "pipeline"],
        key=lambda r: TAXONOMY[r]["order"],
    )
    loop_roles = sorted(
        [r for r in team if TAXONOMY[r]["phase"] == "loop"],
        key=lambda r: TAXONOMY[r]["order"],
    )

    # Register nodes for active roles only.
    for role in pipeline_roles + loop_roles:
        graph.add_node(role.lower(), NODE_REGISTRY[role])

    # Always add the human_review node (no-ops for non-sensitive).
    graph.add_node("human_review", human_review_node)

    # Wire pipeline: START → role1 → role2 → ... → first loop role.
    prev = START
    for role in pipeline_roles:
        graph.add_edge(prev, role.lower())
        prev = role.lower()

    # Hand off from last pipeline role to the first loop role (Writer).
    writer_name = loop_roles[0].lower()
    critic_name = loop_roles[1].lower()
    graph.add_edge(prev, writer_name)

    # Wire loop: Writer → Critic → (conditional) → Writer | human_review | END.
    graph.add_edge(writer_name, critic_name)
    graph.add_conditional_edges(
        critic_name,
        critic_router,
        {"writer": writer_name, "human_review": "human_review", "end": END},
    )
    graph.add_conditional_edges(
        "human_review",
        human_router,
        {"writer": writer_name, "end": END},
    )

    return graph


def compile_graph(team: list[str]):
    """Build and compile the graph."""
    graph = build_graph(team)
    return graph.compile()


# ---------------------------------------------------------------------------
# Run entry point — used by api.py.
# ---------------------------------------------------------------------------

def create_initial_state(question: str, max_iterations: int = 3) -> tuple[State, list[str]]:
    """Analyze the question, select a team, and return the initial state."""
    team = select_team(question)
    raci = build_raci(team)

    initial_state: State = {
        "question": question,
        "team": team,
        "queries": [],
        "sources": [],
        "facts": [],
        "rag_contexts": [],
        "rag_citations": [],
        "rag_parser_summary": {},
        "rag_reference": "",
        "rag_metrics": {},
        "disclaimer": "",
        "answer": "",
        "critic_feedback": "",
        "approved": False,
        "issues": [],
        "iterations": 0,
        "max_iterations": max_iterations,
        "sources_count": 0,
        "llm_calls": 0,
        "duration_seconds": 0.0,
        "was_sensitive": is_sensitive(question),
        "critic_first_pass": False,
        "final_answer": "",
        "episodic_memory": [],
    }

    return initial_state, team
