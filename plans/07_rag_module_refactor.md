# Feature: RAG Module Refactor — 19 Files → 7 Files

**Date:** 2026-05-29
**Status:** 🔲 Planned

## Description

Consolidate the `backend/rag/` module from 19 scattered files into 7 clean, single-responsibility files: `parser.py`, `chunker.py`, `indexer.py`, `pipeline.py`, `retriever.py`, `evaluator.py`, `models.py` (+ `llm.py` stays as shared utility). Every function survives — just moves to its correct home. No logic is lost, no external imports break.

## Checklist

- [ ] Step 1: Create `chunker.py` — move chunking logic from current `parser.py`, rename `parse_sources()` → `chunk_sources()`
- [ ] Step 2: Rewrite `parser.py` — merge `classifier.py` + `ingestion.py` + `folders.py` (load + classify)
- [ ] Step 3: Rewrite `indexer.py` — merge current `indexer.py` + `store.py` + `runtime.py` (ChromaDB + BM25 + KG)
- [ ] Step 4: Create `pipeline.py` — merge `engine.py` + `registry.py` + orchestration wiring
- [ ] Step 5: Rewrite `retriever.py` — merge current retriever + `query_transform.py` + `citations.py` + `search.py`
- [ ] Step 6: Rewrite `evaluator.py` — merge current evaluator + `scorecard.py`
- [ ] Step 7: Update `__init__.py` — point exports to new file locations
- [ ] Step 8: Update `backend/api.py` — fix 5 import paths
- [ ] Step 9: Update test files — fix import paths
- [ ] Step 10: Delete the 11 old files
- [x] Test A: Start server, upload `test_doc.txt` via curl → verify chunks are created
- [x] Test B: Search "When was NovaTech founded?" → verify the **actual PDF text** appears in the returned chunks (not a hallucinated summary)
- [x] Test C: Run Ragas evaluation on the search results → verify all 4 scores (Faithfulness, Relevance, Precision, Recall) are above 0.7 and the **evaluated contexts contain real PDF text**
- [x] Test D: Hit `POST /research` with a normal question → verify the existing multi-agent pipeline still works end-to-end (nothing broke in the orchestrator → reader agent → RAG path)
- [x] Test E: Upload a **real PDF** (not just .txt) → verify the PDF reader extracts text correctly and search returns actual PDF content

## Where each old function lands

```
OLD FILE               → NEW FILE        FUNCTIONS MOVED
────────────────────   ──────────────    ────────────────────────────────────
classifier.py          → parser.py       _detect_kind(), classify_sources()
ingestion.py           → parser.py       load_local_sources(), move_processed()
folders.py             → parser.py       data_root(), pending_files(), SUPPORTED_SUFFIXES
runtime.py             → indexer.py      rag_storage_root(), collection_name(), has_neo4j_credentials()
store.py               → indexer.py      build_storage(), persist_storage()
current parser.py      → chunker.py      _build_parser() → _build_splitter(), parse_sources() → chunk_sources()
current indexer.py     → indexer.py      build_corpus() orchestration moves to pipeline.py
engine.py              → pipeline.py     read_with_rag(), _extract_facts()
registry.py            → pipeline.py     _corpora dict, register(), get(), list_ids()
query_transform.py     → retriever.py    build_query_bundle(), HyDE logic
citations.py           → retriever.py    contexts_and_citations()
search.py              → retriever.py    search_corpus()
scorecard.py           → evaluator.py    score_async(), Ragas metrics
```

## External imports that must keep working

| External File | Current Import | After Refactor |
|---|---|---|
| `agents/reader.py` | `from backend.rag import RagReadResult, read_with_rag` | ✅ `__init__.py` re-exports from `pipeline.py` |
| `api.py` | `from backend.rag import evaluate_answer` | ✅ Same |
| `api.py` | `from backend.rag.classifier import classify_sources` | ⚠️ → `from backend.rag.parser import classify_sources` |
| `api.py` | `from backend.rag.parser import parse_sources` | ⚠️ → `from backend.rag.chunker import chunk_sources` |
| `api.py` | `from backend.rag.indexer import build_corpus` | ⚠️ → `from backend.rag.pipeline import build_corpus` |
| `api.py` | `from backend.rag.search import search_corpus` | ⚠️ → `from backend.rag.retriever import search_corpus` |
| `api.py` | `from backend.rag import registry` | ⚠️ → `from backend.rag import pipeline as rag_registry` |
| `api.py` | `from backend.rag.models import ...` | ✅ Unchanged |
| `api.py` | `from backend.rag.llm import ...` | ✅ Unchanged |

## Files Touched

> Updated after implementation.

| File | Action | What Changed |
|------|--------|-------------|
| `backend/rag/chunker.py` | Created | Chunking strategies + fallback splitter from old `parser.py` |
| `backend/rag/parser.py` | Rewritten | Load + classify (merged `classifier.py`, `ingestion.py`, `folders.py`) |
| `backend/rag/indexer.py` | Rewritten | ChromaDB + BM25 + KG indexes (merged `store.py`, `runtime.py`) |
| `backend/rag/pipeline.py` | Created | Orchestrator: parser→chunker→indexer + registry + read_with_rag |
| `backend/rag/retriever.py` | Rewritten | HyDE + search + fuse + rerank + citations (merged 4 files) |
| `backend/rag/evaluator.py` | Rewritten | Ragas scorecard + evaluate_answer (merged `scorecard.py`) |
| `backend/rag/__init__.py` | Modified | Re-exports point to new locations |
| `backend/api.py` | Modified | 5 import paths updated |
| `backend/rag/models.py` | Unchanged | — |
| `backend/rag/llm.py` | Unchanged | — |
| `backend/rag/classifier.py` | Deleted | Merged into parser.py |
| `backend/rag/ingestion.py` | Deleted | Merged into parser.py |
| `backend/rag/folders.py` | Deleted | Merged into parser.py |
| `backend/rag/runtime.py` | Deleted | Merged into indexer.py |
| `backend/rag/store.py` | Deleted | Merged into indexer.py |
| `backend/rag/engine.py` | Deleted | Merged into pipeline.py |
| `backend/rag/registry.py` | Deleted | Merged into pipeline.py |
| `backend/rag/query_transform.py` | Deleted | Merged into retriever.py |
| `backend/rag/citations.py` | Deleted | Merged into retriever.py |
| `backend/rag/search.py` | Deleted | Merged into retriever.py |
| `backend/rag/scorecard.py` | Deleted | Merged into evaluator.py |

## Notes

- `llm.py` stays as a separate shared utility — both `pipeline.py` and `retriever.py` need it.
- BM25 index currently built at query time in `retriever.py` — will be pre-built in `indexer.py` and stored in `IndexedCorpus`.
- `build_transform_engine()` in `query_transform.py` is dead code (never called) — will be removed.
- The 50-line rule in `skills.md` may need updating after this refactor since files will be ~60–80 lines, but each file now teaches one complete concept instead of a fragment.

## Comment Rules

Every **logical block** (not every line) gets a plain-English comment **before** it explaining:
1. **What** this block does
2. **Why** it's needed (the reasoning, not restating the code)

Example — good:
```python
# Semantic chunking: uses embedding similarity to detect topic shifts.
# breakpoint_percentile_threshold=90 means split only on big topic changes.
return SemanticSplitterNodeParser(
    embed_model=get_llama_embed_model(),
    breakpoint_percentile_threshold=90,
)
```

Example — bad (line-by-line noise):
```python
# Create a semantic splitter
splitter = SemanticSplitterNodeParser(...)  # set the embed model
# Set threshold to 90
splitter.breakpoint_percentile_threshold = 90  # this is 90
```

Logical blocks that need comments:
- Each chunking strategy in `chunker.py` (why this strategy exists)
- The heuristic rules in `parser.py` (why each regex/check classifies a certain way)
- The 3 index builds in `indexer.py` (what each index is for — semantic vs keyword vs entity)
- HyDE transform in `retriever.py` (what HyDE does and why it helps)
- Fusion + rerank logic in `retriever.py` (why we merge 3 sources and rerank)
- Each Ragas metric in `evaluator.py` (what it measures in plain English)
