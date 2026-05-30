"""__init__.py

Parent package exporter for LangGraph agent evaluations using DeepEval.
Consolidates Lexical/Code validation, Hallucination analysis, and Regulatory audits.
Wired into DeepEval tracing so it appears as a span in the trace tree.
"""

from deepeval.tracing import observe, update_current_span
from deepeval.test_case import LLMTestCase

from .lexical_code import evaluate_lexical
from .hallucination import evaluate_hallucination_and_faithfulness
from .compliance import evaluate_regulatory_compliance


@observe(name="agent_evaluation_suite")
def run_agent_evaluations(
    user_input: str,
    actual_output: str,
    expected_output: str,
    retrieved_contexts: list[str],
    model: str = "gpt-4o-mini"
) -> dict:
    """Convenience suite runner that executes all three DeepEval automated assessments.

    Wrapped with @observe so the whole evaluation phase shows up as one span in
    the trace tree, sitting alongside the agent-execution spans (planner,
    searcher, reader, writer, critic).

    Args:
        user_input (str): The initial user research prompt.
        actual_output (str): The final synthesized response from the LangGraph agents.
        expected_output (str): The reference/ground-truth summary.
        retrieved_contexts (list[str]): The complete list of sources gathered during execution.
        model (str): The judge model to run LLM-as-a-judge criteria.

    Returns:
        dict: A combined dictionary of all metrics, scores, reasons, and pass/fail statuses.
    """
    # 1. Lexical validation (BLEU + ROUGE)
    lexical_results = evaluate_lexical(
        actual_output=actual_output,
        expected_output=expected_output,
    )

    # 2. Hallucination & Faithfulness
    hallucination_results = evaluate_hallucination_and_faithfulness(
        actual_output=actual_output,
        retrieved_contexts=retrieved_contexts,
        model=model,
    )

    # 3. EU AI Act & Indian DPDP compliance
    compliance_results = evaluate_regulatory_compliance(
        actual_output=actual_output,
        user_input=user_input,
        model=model,
    )

    # 4. Consolidate
    report = {}
    report.update(lexical_results)
    report.update(hallucination_results)
    report.update(compliance_results)

    report["all_passed"] = all([
        lexical_results["bleu_passed"],
        lexical_results["rouge_passed"],
        hallucination_results["hallucination_passed"],
        hallucination_results["faithfulness_passed"],
        compliance_results["eu_ai_act_passed"],
        compliance_results["dpdp_passed"],
    ])

    # 5. Register a test case on this span so DeepEval can attach it to the trace
    update_current_span(
        test_case=LLMTestCase(
            input=user_input,
            actual_output=actual_output,
            expected_output=expected_output,
            retrieval_context=retrieved_contexts,
        )
    )

    return report


__all__ = [
    "evaluate_lexical",
    "evaluate_hallucination_and_faithfulness",
    "evaluate_regulatory_compliance",
    "run_agent_evaluations",
]
