"""Pipeline — orchestrate the full RAG build and read flow.

This is the conductor that calls everything in order:
  parser → chunker → indexer

It also holds the in-memory corpus registry so that once a document
is indexed, it can be queried multiple times without rebuilding.

Two public entry points:
  build_corpus()   — upload path: parse → chunk → index → return corpus
  read_with_rag()  — agent path: build_corpus + retrieve + extract facts
"""

from __future__ import annotations

from collections import Counter

from .chunker import chunk_sources
from .evaluator import build_reference
from .indexer import build_indexes
from .llm import complete
from .models import IndexedCorpus, RagReadResult, Source
from .parser import classify_sources, load_local_sources, move_processed
from .retriever import retrieve_context


# ─── In-memory corpus registry ──────────────────────────────
# Keeps indexed corpora alive in memory so multiple queries can
# hit the same corpus without re-indexing. Module-level dict.

_corpora: dict[str, IndexedCorpus] = {}


def register(corpus_id: str, corpus: IndexedCorpus) -> None:
    _corpora[corpus_id] = corpus


def get(corpus_id: str) -> IndexedCorpus | None:
    return _corpora.get(corpus_id)


def list_ids() -> list[str]:
    return list(_corpora.keys())


def remove(corpus_id: str) -> None:
    _corpora.pop(corpus_id, None)


# ─── Build pipeline ─────────────────────────────────────────
# This is the main ingestion pipeline: parser → chunker → indexer.
# Called by both the /rag/upload API endpoint and read_with_rag().

def build_corpus(question: str, sources: list[Source]) -> IndexedCorpus:
    """Run the full pipeline: load local files, classify, chunk, index."""
    from .llm import configure_settings
    configure_settings()

    print(f"\n=== Starting RAG Pipeline Build Phase ===")

    # Pick up any files from the hot-folder and merge with provided sources.
    local_sources, local_files = load_local_sources()
    all_sources = sources + local_sources

    # Step 1: Classify — detect document type and pick chunking strategy.
    classified = classify_sources(all_sources)

    # Step 2: Chunk — split documents into nodes using the chosen strategy.
    documents, nodes = chunk_sources(classified)

    # Step 3: Index — embed nodes, build vector/BM25/graph indexes.
    storage, vector_index, graph_index, processed_nodes = build_indexes(
        question, all_sources, documents, nodes,
    )

    # Move hot-folder files to processed/ so they aren't re-indexed.
    move_processed(local_files)

    print("Build complete! Corpus stored in memory.")

    return IndexedCorpus(
        question, all_sources, classified, documents, processed_nodes,
        storage, vector_index, graph_index,
    )


# ─── Fact extraction ────────────────────────────────────────
# Used by the multi-agent reader path — extracts structured facts
# from retrieved contexts using an LLM call.

def _extract_facts(question: str, contexts: list[str]) -> list[str]:
    joined = "\n\n".join(contexts[:3]) or "No context."
    prompt = f"""Extract 5 to 8 concise facts that answer the question.
Return one fact per line with no numbering.

Question: {question}

Context:
{joined}"""
    text = complete(prompt, max_tokens=500)
    return [line.strip("- ").strip() for line in text.splitlines() if line.strip()]


# ─── Read with RAG (agent entry point) ──────────────────────
# Called by the Reader agent in the multi-agent pipeline.
# Builds a corpus, retrieves context, extracts facts, and evaluates.

def read_with_rag(question: str, sources: list[Source]) -> RagReadResult:
    if not sources:
        return RagReadResult([], [], [], {}, "", ["No sources available for RAG ingestion."])
    
    print("\n=== Starting RAG Agent Read Phase ===")
    corpus = build_corpus(question, sources)
    contexts, citations = retrieve_context(corpus, question)
    facts = _extract_facts(question, contexts)
    summary = Counter(item.chunk_strategy for item in corpus.classified)
    reference = build_reference(question, contexts)
    return RagReadResult(facts, contexts, citations, dict(summary), reference)
