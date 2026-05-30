"""lexical_code.py

BLEU and ROUGE evaluation for agent outputs.
Uses DeepEval's LLMTestCase for consistency with the rest of the suite.
"""

from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from deepeval.test_case import LLMTestCase


def evaluate_lexical(
    actual_output: str,
    expected_output: str,
    bleu_threshold: float = 0.3,
    rouge_threshold: float = 0.5,
) -> dict:
    """Score the agent output for BLEU and ROUGE-L against the expected output."""

    # Wrap inputs in a DeepEval test case — same pattern as hallucination.py / compliance.py
    test_case = LLMTestCase(
        input="Evaluate lexical alignment of the agent output.",
        actual_output=actual_output,
        expected_output=expected_output,
    )

    # BLEU — n-gram precision with smoothing
    reference = [test_case.expected_output.split()]
    candidate = test_case.actual_output.split()
    bleu = sentence_bleu(
        reference,
        candidate,
        smoothing_function=SmoothingFunction().method1,
    )

    # ROUGE-L — longest common subsequence F-measure with stemming
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    rouge = scorer.score(test_case.expected_output, test_case.actual_output)["rougeL"].fmeasure

    return {
        "bleu_score": round(bleu, 4),
        "bleu_passed": bleu >= bleu_threshold,
        "rouge_score": round(rouge, 4),
        "rouge_passed": rouge >= rouge_threshold,
    }