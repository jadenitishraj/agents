"""hallucination.py

Evaluates factual consistency and detects logical hallucinations in generated 
agent responses compared to retrieved sources using DeepEval.
"""

from deepeval.metrics import HallucinationMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

def evaluate_hallucination_and_faithfulness(
    actual_output: str, 
    retrieved_contexts: list[str], 
    model: str = "gpt-4o-mini"
) -> dict:
    """Evaluates whether the agent hallucinated relative to its gathered context sources.
    
    Args:
        actual_output (str): The final generated response from the Writer/Critic agent.
        retrieved_contexts (list[str]): Deduped web snippets or facts retrieved by Searcher/Reader.
        model (str): The judge LLM to use for factual extraction.
        
    Returns:
        dict: A dictionary of hallucination scores and validation passes.
    """
    # 1. Define the LLM Test Case
    test_case = LLMTestCase(
        input="Provide a synthesized answer strictly grounded in the retrieved sources.",
        actual_output=actual_output,
        context=retrieved_contexts,
        retrieval_context=retrieved_contexts
    )

    # 2. Initialize Native DeepEval Hallucination & Faithfulness metrics
    # - HallucinationMetric: Identifies if actual_output contains any fabricated statements not in contexts.
    # - FaithfulnessMetric: Measures if actual_output remains strictly truthful to facts in contexts.
    hallucination_metric = HallucinationMetric(threshold=0.3, model=model)
    faithfulness_metric = FaithfulnessMetric(threshold=0.6, model=model)

    # 3. Execute Evaluations
    hallucination_metric.measure(test_case)
    faithfulness_metric.measure(test_case)

    return {
        "hallucination_score": round(hallucination_metric.score, 4), # 0.0 is perfect (no hallucinations)
        "hallucination_passed": hallucination_metric.is_successful(),
        "hallucination_reason": hallucination_metric.reason,
        "faithfulness_score": round(faithfulness_metric.score, 4), # 1.0 is perfect (fully faithful)
        "faithfulness_passed": faithfulness_metric.is_successful(),
        "faithfulness_reason": faithfulness_metric.reason
    }

# =====================================================================
# 📚 STUDENT PEDAGOGICAL TODO: AGENTIC TASK COMPLETION & STEP LOOPS
# =====================================================================
# TODO: In recursive agent patterns (such as Reflexion Writer-Critic loops), 
# students can use DeepEval to analyze operational loop efficiency and completion:
#
# 1. TaskCompletionMetric:
#    Ensures the final response covers all points requested in the initial user 
#    question, scoring the logical completeness of the agent's research cycle.
# 
# 2. StepEfficiencyMetric:
#    Measures if the agent accomplished the task in the minimum possible steps. 
#    If the Writer-Critic node loops 5 times due to ambiguous critique, the step 
#    efficiency score drops, indicating an optimized prompt or routing is needed.
#
# 3. Code Integration:
#    from deepeval.metrics.beta import TaskCompletionMetric, StepEfficiencyMetric
# =====================================================================
