"""__init__.py

Parent package exporter for LangGraph agent evaluations using DeepEval.
Consolidates Lexical/Code validation, Hallucination analysis, and Regulatory audits.
"""

from .lexical_code import evaluate_lexical_and_code
from .hallucination import evaluate_hallucination_and_faithfulness
from .compliance import evaluate_regulatory_compliance

def run_agent_evaluations(
    user_input: str,
    actual_output: str,
    expected_output: str,
    retrieved_contexts: list[str],
    model: str = "gpt-4o-mini"
) -> dict:
    """Convenience suite runner that executes all three DeepEval automated assessments.
    
    Args:
        user_input (str): The initial user research prompt.
        actual_output (str): The final synthesized response from the LangGraph agents.
        expected_output (str): The reference/ground-truth summary.
        retrieved_contexts (list[str]): The complete list of sources gathered during execution.
        model (str): The judge model to run LLM-as-a-judge criteria.
        
    Returns:
        dict: A combined dictionary of all metrics, scores, reasons, and pass/fail statuses.
    """
    # 1. Run Lexical & Code validation
    lexical_results = evaluate_lexical_and_code(
        actual_output=actual_output,
        expected_output=expected_output,
        model=model
    )
    
    # 2. Run Hallucination & Faithfulness checks
    hallucination_results = evaluate_hallucination_and_faithfulness(
        actual_output=actual_output,
        retrieved_contexts=retrieved_contexts,
        model=model
    )
    
    # 3. Run EU AI Act & Indian DPDP compliance
    compliance_results = evaluate_regulatory_compliance(
        actual_output=actual_output,
        user_input=user_input,
        model=model
    )
    
    # 4. Consolidate results into a single report
    report = {}
    report.update(lexical_results)
    report.update(hallucination_results)
    report.update(compliance_results)
    
    # Global pass status
    # Note: exact_match is excluded — free-form agent text will never match
    # character-for-character, so it would always force all_passed to False.
    report["all_passed"] = all([
        lexical_results["lexical_alignment_passed"],
        lexical_results["code_correctness_passed"],
        hallucination_results["hallucination_passed"],
        hallucination_results["faithfulness_passed"],
        compliance_results["eu_ai_act_passed"],
        compliance_results["dpdp_passed"]
    ])
    
    return report

__all__ = [
    "evaluate_lexical_and_code",
    "evaluate_hallucination_and_faithfulness",
    "evaluate_regulatory_compliance",
    "run_agent_evaluations"
]
