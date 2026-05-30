"""
Golden-set RAGAS evaluation (REFERENCE-BASED).

How this differs from eval.py:
    eval.py        -> reference-free. Grades the live loop against ITSELF
                      (is the answer faithful to what was retrieved, is it
                      on-topic, were the chunks relevant). Never asks "is
                      the answer actually correct?"
    golden_eval.py -> reference-based. Grades the live RAG pipeline against a
                      HAND-CURATED set of expected answers + expected contexts.
                      This is your regression suite / the thing to show users.

>>> IMPORTANT, sir:
    A golden set is only meaningful if its references come from YOUR real
    indexed documents and are verified by a human. The Veridia entries below
    are placeholders that match the dummy data in eval.py — replace them with
    real question / answer / source-chunk triples from your own corpus.

Drop this file next to eval.py (same package, e.g. backend/rag_v2/) so the
relative import `.llm` and the `backend.rag_v2.*` imports resolve.
"""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ragas import SingleTurnSample
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    Faithfulness,
    ResponseRelevancy,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
    FactualCorrectness,
    SemanticSimilarity,
)

from .llm import get_langchain_embeddings, get_langchain_llm


# ---------------------------------------------------------------------------
# 1. THE GOLDEN SET  — edit this. One dict per question.
#       question           : what you ask the RAG
#       reference          : the verified correct answer (ground truth)
#       reference_contexts : the source chunk(s) that SHOULD be retrieved
# ---------------------------------------------------------------------------
GOLDEN_SET: list[dict] = [
    {
        "question": "Who carved the glass clocks of Veridia?",
        "reference": (
            "The glass clocks of Veridia were hand-carved by the chronomancer "
            "Elara using pure starlight."
        ),
        "reference_contexts": [
            "Legend says the glass clocks of Veridia, which never lose a single "
            "second, were hand-carved by the elusive chronomancer Elara using "
            "pure starlight.",
        ],
    },
    {
        "question": "What is Veridia known for?",
        "reference": (
            "Veridia is known for its beautiful glasswork and ancient magical "
            "artifacts."
        ),
        "reference_contexts": [
            "Veridia is a city known for its beautiful glasswork and ancient "
            "magical artifacts.",
        ],
    },
]


# ---------------------------------------------------------------------------
# 2. Score ONE sample against its reference.
#    Reference-based metrics:
#       context_precision   -> of retrieved chunks, how many are relevant
#                              (judged WITH the reference, not free-floating)
#       context_recall      -> did retrieval find what was NEEDED to answer
#                              (impossible without a reference)
#       factual_correctness -> does the answer match ground truth, not just
#                              the context
#       semantic_similarity -> embedding closeness answer <-> reference
#    Reference-free (kept for continuity with eval.py):
#       faithfulness, answer_relevance
# ---------------------------------------------------------------------------
async def _score_sample(
    question: str,
    answer: str,
    contexts: list[str],
    reference: str,
    reference_contexts: list[str],
) -> dict[str, float | None]:
    llm = LangchainLLMWrapper(get_langchain_llm())
    embeds = LangchainEmbeddingsWrapper(get_langchain_embeddings())

    sample = SingleTurnSample(
        user_input=question,
        response=answer,
        retrieved_contexts=contexts,
        reference=reference,
        reference_contexts=reference_contexts,
    )

    metrics = {
        "faithfulness": Faithfulness(llm=llm),
        "answer_relevance": ResponseRelevancy(llm=llm, embeddings=embeds),
        "context_precision": LLMContextPrecisionWithReference(llm=llm),
        "context_recall": LLMContextRecall(llm=llm),
        "factual_correctness": FactualCorrectness(llm=llm),
        "semantic_similarity": SemanticSimilarity(embeddings=embeds),
    }

    scores: dict[str, float | None] = {}
    for name, metric in metrics.items():
        try:
            scores[name] = round(float(await metric.single_turn_ascore(sample)), 4)
        except Exception as e:  # one bad metric shouldn't kill the row
            scores[name] = None
            print(f"    [!] metric '{name}' failed: {e}")
    return scores


def _run(make_coro):
    """Same event-loop dance as eval.py: works inside or outside a loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(make_coro())
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(lambda: asyncio.run(make_coro())).result()


# ---------------------------------------------------------------------------
# 3. Run the whole golden set through the LIVE pipeline.
# ---------------------------------------------------------------------------
def run_golden_evaluation(top_k: int = 3) -> dict:
    from backend.rag_v2.pipeline import search_rag
    from backend.rag_v2.llm import complete

    per_question: list[dict] = []

    for i, item in enumerate(GOLDEN_SET, start=1):
        q = item["question"]
        print(f"\n[{i}/{len(GOLDEN_SET)}] {q}")

        # --- live retrieval ---
        search_result = search_rag(q, top_k=top_k)
        contexts = [r["text"] for r in search_result.get("results", [])]
        joined = search_result.get("joined_text", "\n".join(contexts))
        if not contexts:
            print("    [!] No contexts retrieved — recall/precision will be low by design.")

        # --- live answer ---
        prompt = f"""Answer the question concisely using ONLY the provided context.
If the context does not contain the answer, say "I don't know".

Question: {q}

Context:
{joined}"""
        answer = complete(prompt)
        print(f"    -> Answer: {answer[:120]}{'...' if len(answer) > 120 else ''}")

        # --- score against the golden reference ---
        scores = _run(lambda: _score_sample(
            q, answer, contexts,
            item["reference"], item.get("reference_contexts", []),
        ))

        per_question.append({
            "question": q,
            "generated_answer": answer,
            "reference": item["reference"],
            "retrieved_contexts": contexts,
            "scores": scores,
        })

    return {"per_question": per_question, "aggregate": _aggregate(per_question)}


def _aggregate(per_question: list[dict]) -> dict[str, float]:
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for row in per_question:
        for k, v in row["scores"].items():
            if v is None:
                continue
            totals[k] = totals.get(k, 0.0) + v
            counts[k] = counts.get(k, 0) + 1
    return {k: round(totals[k] / counts[k], 4) for k in totals}


def _print_scorecard(aggregate: dict[str, float]) -> None:
    print("\n--- Golden-Set Scorecard (averaged over all questions) ---")
    if not aggregate:
        print("  (no metrics computed)")
        return
    width = max(len(k) for k in aggregate)
    for k, v in aggregate.items():
        bar = "#" * int(round(v * 20))
        print(f"  {k.ljust(width)} : {v:.4f}  {bar}")


# ---------------------------------------------------------------------------
# 4. CLI entry point.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("==================================================")
    print("         GOLDEN-SET RAGAS EVALUATION              ")
    print("==================================================")

    report = run_golden_evaluation(top_k=3)

    _print_scorecard(report["aggregate"])

    out_path = Path(__file__).resolve().parent / "golden_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nFull report written to: {out_path}")
    print("==================================================")