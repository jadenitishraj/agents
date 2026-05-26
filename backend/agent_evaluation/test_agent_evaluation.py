"""test_agent_evaluation.py

Runs the REAL LangGraph agent pipeline end-to-end and then evaluates
the actual output using the DeepEval evaluation suite.

To execute this test:
1. Ensure your OPENAI_API_KEY is configured in your .env file.
2. Install deepeval: pip install deepeval
3. Run this file: python3 backend/agent_evaluation/test_agent_evaluation.py
"""

import os
import sys
import time

# Ensure project root is in the path so backend.* imports resolve.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

from backend.orchestrator import compile_graph, create_initial_state
from backend.agent_evaluation import run_agent_evaluations


# ---------------------------------------------------------------------------
# Helper: safely truncate a reason string for terminal display.
# ---------------------------------------------------------------------------

def _trunc(text, length=120):
    """Return a safely truncated string for display."""
    if not text:
        return "(no reason provided)"
    return text[:length] + ("..." if len(text) > length else "")


# ---------------------------------------------------------------------------
# Test definitions — each is a (question, expected_output) pair.
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


# ---------------------------------------------------------------------------
# Main test runner.
# ---------------------------------------------------------------------------

def test_with_live_agents():
    """Invoke the real LangGraph pipeline and evaluate the output."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY is not set. Cannot run LLM-backed evaluations.")
        return

    for idx, tc in enumerate(TEST_CASES, 1):
        question = tc["question"]
        expected = tc["expected_output"]

        print(f"\n{'='*70}")
        print(f"  TEST CASE {idx}: {question}")
        print(f"{'='*70}")

        # ------------------------------------------------------------------
        # Step 1 — Run the REAL LangGraph agent pipeline.
        # ------------------------------------------------------------------
        print("\n🚀 [Step 1/3] Running LangGraph agent pipeline...")

        initial_state, team = create_initial_state(question, max_iterations=2)
        graph = compile_graph(team)

        start = time.time()
        try:
            final_state = graph.invoke(
                initial_state,
                config={"recursion_limit": 50},
            )
        except Exception as exc:
            print(f"\n❌ Pipeline crashed: {exc}")
            continue
        elapsed = time.time() - start

        final_answer = final_state.get("answer", "") or final_state.get("final_answer", "")
        sources = final_state.get("sources", [])
        facts = final_state.get("facts", [])

        print(f"\n✅ Pipeline finished in {elapsed:.1f}s")
        print(f"   Team:       {', '.join(final_state.get('team', []))}")
        print(f"   Iterations: {final_state.get('iterations', 0)}")
        print(f"   LLM calls:  {final_state.get('llm_calls', 0)}")
        print(f"   Sources:    {final_state.get('sources_count', 0)}")
        print(f"   Answer len: {len(final_answer.split())} words")

        # ------------------------------------------------------------------
        # Step 2 — Build retrieval contexts from the REAL agent state.
        # ------------------------------------------------------------------
        print("\n🔍 [Step 2/3] Extracting contexts from agent state...")

        # Combine source snippets + extracted facts as the retrieval context.
        retrieved_contexts = []
        for src in sources:
            snippet = src.get("snippet", "")
            if snippet:
                retrieved_contexts.append(snippet)
        for fact in facts:
            if fact:
                retrieved_contexts.append(fact)

        if not retrieved_contexts:
            # Fallback: use the answer itself so DeepEval doesn't get None.
            retrieved_contexts = [final_answer]
            print("   ⚠️  No sources/facts found; using answer as fallback context.")
        else:
            print(f"   Found {len(retrieved_contexts)} context chunks.")

        # ------------------------------------------------------------------
        # Step 3 — Run DeepEval evaluation suite on the REAL output.
        # ------------------------------------------------------------------
        print("\n🧪 [Step 3/3] Running DeepEval evaluation suite...")

        try:
            report = run_agent_evaluations(
                user_input=question,
                actual_output=final_answer,
                expected_output=expected,
                retrieved_contexts=retrieved_contexts,
                model="gpt-4o-mini",
            )
        except Exception as exc:
            print(f"\n❌ DeepEval evaluation failed: {exc}")
            continue

        # ------------------------------------------------------------------
        # Report.
        # ------------------------------------------------------------------
        print(f"\n{'='*70}")
        print("  📝 DEEPEVAL AGENT VERIFICATION REPORT")
        print(f"{'='*70}")
        print(f"  📊 Exact Match:         {report['exact_match_score']}  (Passed: {report['exact_match_passed']})")
        print(f"  📊 Lexical Alignment:   {report['lexical_alignment_score']}  (Passed: {report['lexical_alignment_passed']})")
        print(f"     └─ {_trunc(report.get('lexical_alignment_reason'))}")
        print(f"  📊 Code Correctness:    {report['code_correctness_score']}  (Passed: {report['code_correctness_passed']})")
        print(f"     └─ {_trunc(report.get('code_correctness_reason'))}")
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


if __name__ == "__main__":
    test_with_live_agents()
