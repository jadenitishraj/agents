"""test_agent_evaluation.py

DeepEval-runnable test of the real LangGraph research agent.

Run with:
    deepeval test run backend/agent_evaluation/test_agent_evaluation.py

This produces:
 1. A hierarchical trace tree showing every agent node and its per-node
    metric score (from @observe decorators on planner, searcher, reader,
    writer, critic).
 2. A printed verification report with BLEU, ROUGE, Hallucination,
    Faithfulness, EU AI Act, and DPDP scores (from run_agent_evaluations).
 3. A pass/fail verdict per test case based on all_passed.
"""

import os
import sys

import pytest
from dotenv import load_dotenv
from deepeval.tracing import observe

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

from backend.orchestrator import compile_graph, create_initial_state
from backend.agent_evaluation import run_agent_evaluations


# ---------------------------------------------------------------------------
# Helper: safely truncate a reason string for terminal display.
# ---------------------------------------------------------------------------
def _trunc(text, length=120):
    if not text:
        return "(no reason provided)"
    return text[:length] + ("..." if len(text) > length else "")


# ---------------------------------------------------------------------------
# Test cases — expand this list for a real benchmark.
# ---------------------------------------------------------------------------
TEST_CASES = [
    {
        "question": "What is Python and what are its main use cases?",
        "expected_output": (
            "Python is a high-level, interpreted programming language known for "
            "its readability and versatility. It is widely used in web development, "
            "data science, machine learning, automation, and scripting."
        ),
    },
]


@pytest.mark.parametrize("tc", TEST_CASES)
@observe(type="agent", name="research_agent_run")
def test_research_agent(tc):
    """End-to-end run: invoke the real LangGraph, then score the output."""
    question = tc["question"]
    expected = tc["expected_output"]

    print(f"\n{'='*70}")
    print(f"  TEST CASE: {question}")
    print(f"{'='*70}")

    # 1. Run the real graph — @observe decorators on each node populate the tree
    initial_state, team = create_initial_state(question, max_iterations=2)
    graph = compile_graph(team)
    final_state = graph.invoke(initial_state, config={"recursion_limit": 50})

    final_answer = final_state.get("answer", "") or final_state.get("final_answer", "")
    sources = final_state.get("sources", [])
    facts = final_state.get("facts", [])

    # 2. Build retrieval context from real agent state
    retrieved_contexts = []
    for src in sources:
        snippet = src.get("snippet", "")
        if snippet:
            retrieved_contexts.append(snippet)
    for fact in facts:
        if fact:
            retrieved_contexts.append(fact)
    if not retrieved_contexts:
        retrieved_contexts = [final_answer]

    # 3. Run the evaluation suite
    report = run_agent_evaluations(
        user_input=question,
        actual_output=final_answer,
        expected_output=expected,
        retrieved_contexts=retrieved_contexts,
        model="gpt-4o-mini",
    )

    # 4. Print the verification report (always visible, not just on failure)
    print(f"\n{'='*70}")
    print("  📝 DEEPEVAL AGENT VERIFICATION REPORT")
    print(f"{'='*70}")
    print(f"  📊 BLEU Score:          {report['bleu_score']}  (Passed: {report['bleu_passed']})")
    print(f"  📊 ROUGE-L Score:       {report['rouge_score']}  (Passed: {report['rouge_passed']})")
    print(f"  📊 Hallucination:       {report['hallucination_score']}  (Passed: {report['hallucination_passed']})")
    print(f"     └─ {_trunc(report.get('hallucination_reason'))}")
    print(f"  📊 Faithfulness:        {report['faithfulness_score']}  (Passed: {report['faithfulness_passed']})")
    print(f"     └─ {_trunc(report.get('faithfulness_reason'))}")
    print(f"  📊 EU AI Act:           {report['eu_ai_act_score']}  (Passed: {report['eu_ai_act_passed']})")
    print(f"     └─ {_trunc(report.get('eu_ai_act_reason'))}")
    print(f"  📊 Indian DPDP:         {report['dpdp_score']}  (Passed: {report['dpdp_passed']})")
    print(f"     └─ {_trunc(report.get('dpdp_reason'))}")
    print(f"  {'─'*68}")
    print(f"  🏆 ALL GATES PASSED:    {report['all_passed']}")
    print(f"{'='*70}\n")

    # 5. Assert — deepeval test run marks the test as pass/fail on this line
    failed = [
            name for name, passed in [
                ("BLEU", report["bleu_passed"]),
                ("ROUGE", report["rouge_passed"]),
                ("Hallucination", report["hallucination_passed"]),
                ("Faithfulness", report["faithfulness_passed"]),
                ("EU AI Act", report["eu_ai_act_passed"]),
                ("DPDP", report["dpdp_passed"]),
            ] if not passed
        ]
    assert report["all_passed"], f"FAILED METRICS: {', '.join(failed)}"
