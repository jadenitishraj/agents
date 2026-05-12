"""FastAPI application — simple request/response API.

One endpoint: POST /research → invoke graph → return result.
No streaming, no SSE, no approve endpoint.
"""

from __future__ import annotations

import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.orchestrator import compile_graph, create_initial_state

app = FastAPI(title="Multi-Agent Research System")

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
    print(f"\n{'='*60}")
    print(f"New research request: {req.question}")
    print(f"{'='*60}")

    initial_state, team = create_initial_state(req.question, req.max_iterations)
    graph = compile_graph(team)

    print(f"Team: {', '.join(team)}")
    print(f"Starting pipeline...\n")

    start_time = time.time()
    final_state = graph.invoke(initial_state, config={"recursion_limit": 50})
    final_state["duration_seconds"] = time.time() - start_time
    final_state["final_answer"] = final_state.get("answer", "")

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
    }
