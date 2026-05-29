"""FastAPI application — simple request/response API.

Endpoints:
  POST /research  → invoke graph → return result.
  POST /rag/upload → upload a file, index it, return corpus_id.
  POST /rag/search → pure retrieval search (no answer generation).
"""

from __future__ import annotations

import os
import time
# Removed unused standard imports
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # Load .env BEFORE any LangChain/LangSmith imports

import uuid

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
# Removed unused starlette imports

from backend.guardrails.pipeline import input_guard, output_guard, is_safe
from backend.orchestrator import compile_graph, create_initial_state
from backend.rag import evaluate_answer
from backend.rag.parser import classify_sources
from backend.rag.chunker import chunk_sources
from backend.rag.pipeline import build_corpus
from backend.rag.retriever import search_corpus
from backend.rag import pipeline as rag_registry
from backend.rag.models import IndexedCorpus, Source
from backend.rag.llm import configure_settings

# --- Observability Setup ---
from logger.loki import logger
from logger.prometheus import setup_prometheus_metrics, llm_calls_counter, iterations_counter, sources_counter
from logger.middleware import LoggingMiddleware

app = FastAPI(title="Multi-Agent Research System")
setup_prometheus_metrics(app)

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the frontend static files.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# ---------------------------------------------------------------------------
# Request / response models.
# ---------------------------------------------------------------------------

class ResearchRequest(BaseModel):
    question: str
    max_iterations: int = 3


# ---------------------------------------------------------------------------
# POST /research — run the full pipeline and return the result.
# ---------------------------------------------------------------------------

@app.post("/research")
async def research(req: ResearchRequest):
    logger.info(f"Incoming Payload: {req.model_dump_json()}")
    logger.info(f"Starting research pipeline for question: {req.question}")
    print(f"\n{'='*60}")
    print(f"New research request: {req.question}")
    print(f"{'='*60}")

    is_allowed, msg = is_safe(input_guard, req.question)
    if not is_allowed:
        logger.warning(f"Input blocked by guardrails: {msg}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "input_blocked",
                "message": msg,
                "guardrails": {"allowed": False, "user_message": msg},
            },
        )

    initial_state, team = create_initial_state(req.question, req.max_iterations)
    graph = compile_graph(team)

    logger.info(f"Compiled team: {', '.join(team)}")
    print(f"Team: {', '.join(team)}")
    print(f"Starting pipeline...\n")

    start_time = time.time()
    try:
        final_state = graph.invoke(
            initial_state,
            config={
                "recursion_limit": 50,
                "metadata": {
                    "question": req.question,
                    "team": team,
                },
            },
        )
    except Exception as e:
        logger.error(f"Graph execution failed with error: {str(e)}", exc_info=True)
        raise e
        
    final_state["duration_seconds"] = time.time() - start_time
    is_allowed, msg = is_safe(output_guard, final_state.get("answer", ""))
    final_state["final_answer"] = final_state.get("answer", "") if is_allowed else msg
    final_state["rag_metrics"] = evaluate_answer(
        final_state.get("question", ""),
        final_state.get("final_answer", ""),
        final_state.get("rag_contexts", []),
        final_state.get("rag_reference", ""),
    )

    # Push Custom Metrics via OpenTelemetry
    llm_calls_counter.add(final_state.get("llm_calls", 0))
    iterations_counter.add(final_state.get("iterations", 0))
    sources_counter.add(final_state.get("sources_count", 0))

    logger.info(f"Research complete in {final_state['duration_seconds']:.1f}s")
    print(f"\nPipeline complete in {final_state['duration_seconds']:.1f}s")
    print(f"{'='*60}\n")

    return {
        "question": final_state.get("question", ""),
        "team": final_state.get("team", []),
        "final_answer": final_state.get("final_answer", ""),
        "iterations": final_state.get("iterations", 0),
        "llm_calls": final_state.get("llm_calls", 0),
        "sources_count": final_state.get("sources_count", 0),
        "duration_seconds": final_state.get("duration_seconds", 0),
        "was_sensitive": final_state.get("was_sensitive", False),
        "rag_metrics": final_state.get("rag_metrics", {}),
        "rag_parser_summary": final_state.get("rag_parser_summary", {}),
        "guardrails": {
            "input": {"allowed": True, "user_message": "OK"},
            "output": {"allowed": is_allowed, "user_message": msg},
        },
    }


# ---------------------------------------------------------------------------
# RAG Search endpoints — upload a file and search it without answer generation.
# ---------------------------------------------------------------------------

ALLOWED_SUFFIXES = {".pdf", ".txt", ".md"}
UPLOAD_DIR = Path(__file__).resolve().parent / "rag" / "data" / "need-processing"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class RagSearchRequest(BaseModel):
    query: str
    corpus_id: str = ""
    top_k: int = 5


@app.post("/rag/upload")
async def rag_upload(file: UploadFile = File(...)):
    """Upload a document, index it, return corpus_id."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported file type: {suffix}. Use .pdf, .txt, or .md"},
        )

    # Save to hot-folder
    save_path = UPLOAD_DIR / (file.filename or "upload.txt")
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    logger.info(f"RAG upload: saved {file.filename} ({len(content)} bytes)")

    # Build corpus using the existing pipeline
    configure_settings()
    source: Source = {
        "title": file.filename or "Uploaded Document",
        "url": str(save_path),
        "snippet": content[:300].decode("utf-8", errors="replace"),
    }

    try:
        corpus = build_corpus("uploaded document", [source])
    except Exception as e:
        logger.error(f"RAG indexing failed: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})

    corpus_id = str(uuid.uuid4())[:8]
    rag_registry.register(corpus_id, corpus)

    logger.info(f"RAG indexed: corpus_id={corpus_id}, chunks={len(corpus.nodes)}")

    return {
        "corpus_id": corpus_id,
        "filename": file.filename,
        "chunks": len(corpus.nodes),
        "categories": list({c.category for c in corpus.classified}),
        "strategies": list({c.chunk_strategy for c in corpus.classified}),
    }


@app.post("/rag/search")
async def rag_search(req: RagSearchRequest):
    """Search the indexed corpus — pure retrieval, no answer generation."""
    # Use latest corpus if none specified
    corpus_id = req.corpus_id or (rag_registry.list_ids()[-1] if rag_registry.list_ids() else "")
    if not corpus_id:
        return JSONResponse(status_code=400, content={"error": "No corpus indexed. Upload a file first."})

    corpus = rag_registry.get(corpus_id)
    if corpus is None:
        return JSONResponse(status_code=404, content={"error": f"Corpus '{corpus_id}' not found."})

    logger.info(f"RAG search: corpus={corpus_id}, query={req.query!r}")

    start = time.time()
    try:
        results = search_corpus(corpus, req.query, top_k=req.top_k)
    except Exception as e:
        logger.error(f"RAG search failed: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})

    elapsed = time.time() - start
    logger.info(f"RAG search complete: {len(results)} results in {elapsed:.2f}s")

    return {
        "corpus_id": corpus_id,
        "query": req.query,
        "results": results,
        "elapsed_seconds": round(elapsed, 2),
    }
