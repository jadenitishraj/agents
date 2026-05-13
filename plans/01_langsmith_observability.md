# Feature: LangSmith Observability

**Date:** 2026-05-13
**Status:** ✅ Complete

## Description

Add LangSmith tracing to the project so every agent, tool call, LLM invocation, and routing decision is visible in the LangSmith dashboard. Uses `@traceable` decorators and LangGraph/LangChain auto-tracing.

## Checklist

- [x] Add `langsmith>=0.3.0` to requirements.txt
- [x] Add `@traceable(name="...", run_type="chain")` to all 7 agent functions
- [x] Add `@traceable(name="search_web", run_type="tool")` to DuckDuckGo wrapper
- [x] Add `load_dotenv()` at top of api.py (before LangChain imports)
- [x] Pass metadata (question, team) to `graph.invoke()` config
- [x] Add LangSmith env vars to .env
- [x] Test: full pipeline runs and traces appear in LangSmith

## Files Touched

| File | Action | What Changed |
|------|--------|-------------|
| `backend/requirements.txt` | Modified | Added `langsmith>=0.3.0` |
| `backend/agents/planner.py` | Modified | Added `@traceable` import and decorator |
| `backend/agents/searcher.py` | Modified | Added `@traceable` import and decorator |
| `backend/agents/reader.py` | Modified | Added `@traceable` import and decorator |
| `backend/agents/writer.py` | Modified | Added `@traceable` import and decorator |
| `backend/agents/critic.py` | Modified | Added `@traceable` import and decorator |
| `backend/agents/compliance.py` | Modified | Added `@traceable` import and decorator |
| `backend/agents/reflector.py` | Modified | Added `@traceable` import and decorator |
| `backend/tools/search.py` | Modified | Added `@traceable` import and decorator (run_type="tool") |
| `backend/api.py` | Modified | Added early `load_dotenv()`, added metadata to `graph.invoke()` config |
| `.env` | Modified | Added LANGSMITH_TRACING, ENDPOINT, API_KEY, PROJECT vars |

## Notes

- No code changes needed in orchestrator.py — LangGraph auto-traces graph execution.
- `@traceable` uses `run_type="chain"` for agents and `run_type="tool"` for search.
