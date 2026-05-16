"""FastAPI application — simple request/response API.

One endpoint: POST /research → invoke graph → return result.
No streaming, no SSE, no approve endpoint.
"""

from __future__ import annotations

import os
import time
# Removed unused standard imports
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # Load .env BEFORE any LangChain/LangSmith imports

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
# Removed unused starlette imports

from backend.guardrails.pipeline import input_guard, output_guard, is_safe
from backend.orchestrator import compile_graph, create_initial_state

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
        "guardrails": {
            "input": {"allowed": True, "user_message": "OK"},
            "output": {"allowed": is_allowed, "user_message": msg},
        },
    }
