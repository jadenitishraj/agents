"""lexical_code.py

Evaluates the lexical alignment, exact match, and functional code correctness
of generated agent responses using DeepEval.

This module is 100% self-contained and avoids custom code execution scripting.
"""

from deepeval.metrics import ExactMatchMetric, GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

def evaluate_lexical_and_code(
    actual_output: str, 
    expected_output: str, 
    model: str = "gpt-4o-mini"
) -> dict:
    """Evaluates Lexical Alignment, Exact Match, and Code Correctness for the agent's output.
    
    Args:
        actual_output (str): The generated response from the LangGraph agent team.
        expected_output (str): The reference/ground-truth summary.
        model (str): The LLM to use for G-Eval code correctness.
        
    Returns:
        dict: A dictionary of metric scores and status results.
    """
    # 1. Define the LLM Test Case
    test_case = LLMTestCase(
        input="Write/evaluate the requested technical code block or solution.",
        actual_output=actual_output,
        expected_output=expected_output
    )

    # 2. Initialize Native DeepEval Lexical & Alignment Metrics
    exact_match_metric = ExactMatchMetric()

    lexical_alignment_metric = GEval(
        name="Lexical & Semantic Alignment",
        criteria=(
            "Verify that the actual_output semantically matches the expected_output. "
            "It must cover the same core factual points, technical requirements, and contextual focus "
            "as defined in the ground-truth expected_output."
        ),
        evaluation_params=[LLMTestCaseParams.EXPECTED_OUTPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.6,
        model=model
    )

    # 3. Initialize G-Eval for Code Correctness
    # Audits any generated code snippets within the response for syntax and functional completeness
    code_correctness_metric = GEval(
        name="Code Correctness Check",
        criteria=(
            "Assess if any Python or structural code blocks inside the actual_output "
            "are syntactically valid, complete (no placeholders or 'TODO's in critical logic), "
            "and logically correct relative to the intended expected_output. "
            "If no code blocks are expected or present, default the score to 1.0."
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7,
        model=model
    )

    # 4. Measure metrics
    exact_match_metric.measure(test_case)
    lexical_alignment_metric.measure(test_case)
    code_correctness_metric.measure(test_case)

    return {
        "exact_match_score": round(exact_match_metric.score, 4),
        "exact_match_passed": exact_match_metric.is_successful(),
        "lexical_alignment_score": round(lexical_alignment_metric.score, 4),
        "lexical_alignment_passed": lexical_alignment_metric.is_successful(),
        "lexical_alignment_reason": lexical_alignment_metric.reason,
        "code_correctness_score": round(code_correctness_metric.score, 4),
        "code_correctness_passed": code_correctness_metric.is_successful(),
        "code_correctness_reason": code_correctness_metric.reason
    }

# =====================================================================
# 📚 STUDENT PEDAGOGICAL TODO: AGENT TRACING & STEP ANALYSIS
# =====================================================================
# TODO: In LangGraph multi-agent setups, simple input-output testing doesn't 
# capture which agent made a mistake. Students can leverage DeepEval Tracing
# to evaluate the performance of intermediate steps:
#
# 1. Install DeepEval trace hook:
#    pip install deepeval
# 
# 2. Wrap your LangGraph node calls with the @observe() decorator:
#    from deepeval.tracing import observe
#    
#    @observe()
#    def searcher_node(state):
#        ...
#
# 3. This registers a complete, interactive hierarchical trace in the DeepEval 
#    dashboard, allowing you to debug intermediate tool parameters and agent 
#    rationales in real-time.
# =====================================================================
