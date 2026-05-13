# Multi-Agent Research System — Implementation Plan

## Goal

Convert `multi‑agent.py` (a 2200-line teaching notebook) into a clean, modular project with:
- A FastAPI backend with SSE streaming
- A simple frontend (HTML/CSS/JS) to interact with the system
- Dynamic orchestration (graph shape changes based on team)
- No A2A / MessageBus code

---

## Project Structure

```
agents/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner.py         # planner_agent(question) → list[str]
│   │   ├── searcher.py        # searcher_agent(queries, search_tool) → list[Source]
│   │   ├── reader.py          # reader_agent(question, sources) → list[str]
│   │   ├── writer.py          # writer_agent(question, sources, facts, disclaimer, feedback) → str
│   │   ├── critic.py          # critic_agent(question, answer, sources) → (bool, list[str])
│   │   ├── compliance.py      # compliance_agent(question) → str
│   │   └── reflector.py       # reflector_agent(question, draft, issues, iteration) → Reflection
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   └── search.py          # DuckDuckGo wrapped as a LangChain tool
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── taxonomy.py        # TAXONOMY dict (with phase, order metadata)
│   │   ├── team_selector.py   # select_team(), needs_deep_reading(), is_sensitive()
│   │   └── raci.py            # RACIEntry dataclass, build_raci()
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── incentives.py      # IncentiveRisk dataclass, scan_incentives()
│   │   └── serialization.py   # serialize_trace(), deserialize_trace(), SCHEMA_VERSION
│   │
│   ├── orchestrator.py        # State TypedDict + dynamic graph builder + node wrappers
│   ├── llm.py                 # Shared ChatOpenAI wrapper (get_llm, call_llm)
│   ├── api.py                 # FastAPI app, SSE streaming, HITL endpoint
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── index.css
│   └── index.js
│
├── main.py                    # Entry point — starts FastAPI via uvicorn
└── README.md
```

---

## File-by-File Breakdown

### Backend

#### `backend/llm.py`
- `get_llm(max_tokens)` — lazy singleton `ChatOpenAI` client
- `call_llm(prompt, max_tokens)` — send prompt, return string
- Model: `gpt-4o-mini`, temperature `0.3`
- Reads `OPENAI_API_KEY` from environment

#### `backend/tools/search.py`
- Wrap DuckDuckGo as a LangChain tool using `DuckDuckGoSearchResults` from `langchain_community.tools`
- Export a `search_web(query: str) -> list[dict]` function that the Searcher agent calls
- This replaces the raw `ddgs.text()` call in the notebook

#### `backend/agents/planner.py`
- `planner_agent(question: str) -> list[str]`
- Calls `call_llm()` to break question into 3-5 search queries
- Pure function — no LangGraph, no State awareness

#### `backend/agents/searcher.py`
- `searcher_agent(queries: list[str]) -> list[Source]`
- Uses the DuckDuckGo tool from `tools/search.py`
- Deduplicates by URL
- Returns list of `{"title", "url", "snippet"}` dicts

#### `backend/agents/reader.py`
- `reader_agent(question: str, sources: list[Source]) -> list[str]`
- Calls `call_llm()` to extract 5-10 key facts from source snippets

#### `backend/agents/writer.py`
- `writer_agent(question, sources, facts, disclaimer, critic_feedback) -> str`
- Calls `call_llm()` to synthesize a 150-300 word answer
- Accepts optional critic feedback (or Reflexion lessons) to address on rewrites

#### `backend/agents/critic.py`
- `critic_agent(question, answer, sources) -> tuple[bool, list[str]]`
- Rule-based checks (min sources, min word count) + LLM verdict
- Returns `(approved, issues)`

#### `backend/agents/compliance.py`
- `compliance_agent(question: str) -> str`
- Generates a one-sentence disclaimer for sensitive topics

#### `backend/agents/reflector.py`
- `Reflection` dataclass: `iteration`, `what_failed`, `lesson_learned`
- `reflector_agent(question, draft, issues, iteration) -> Reflection`
- Converts raw critic issues into a generalized lesson (Reflexion pattern)

#### `backend/config/taxonomy.py`
- `TAXONOMY` dict with enriched metadata:
  ```python
  TAXONOMY = {
      "Planner":    {"mission": "...", "always": True,  "phase": "pipeline", "order": 1},
      "Searcher":   {"mission": "...", "always": True,  "phase": "pipeline", "order": 2},
      "Reader":     {"mission": "...", "always": False, "phase": "pipeline", "order": 3},
      "Compliance": {"mission": "...", "always": False, "phase": "pipeline", "order": 4},
      "Writer":     {"mission": "...", "always": True,  "phase": "loop",     "order": 1},
      "Critic":     {"mission": "...", "always": True,  "phase": "loop",     "order": 2},
  }
  ```
- `DEEP_KEYWORDS` and `SENSITIVE_KEYWORDS` lists

#### `backend/config/team_selector.py`
- `needs_deep_reading(question: str) -> bool`
- `is_sensitive(question: str) -> bool`
- `select_team(question: str) -> list[str]`
- Uses keywords from `taxonomy.py`

#### `backend/config/raci.py`
- `RACIEntry` dataclass: `task`, `responsible`, `accountable`, `consulted`, `informed`
- `build_raci(team: list[str]) -> list[RACIEntry]`

#### `backend/evaluation/incentives.py`
- `IncentiveRisk` dataclass: `name`, `why`, `mitigation`
- `scan_incentives(trace: State) -> list[IncentiveRisk]`
- Checks: speed-over-depth, thin research, missing compliance, rubber-stamping

#### `backend/evaluation/serialization.py`
- `SCHEMA_VERSION = "1.0"`
- `serialize_trace(trace: State) -> str` (JSON)
- `deserialize_trace(json_str: str) -> State`

#### `backend/orchestrator.py`

This is the heart of the project. Contains:

1. **`State` TypedDict** — all fields (question, team, queries, sources, facts, disclaimer, answer, critic_feedback, approved, issues, iterations, max_iterations, sources_count, llm_calls, duration_seconds, was_sensitive, critic_first_pass, final_answer, episodic_memory)

2. **Node registry** — maps role names to node wrapper functions:
   ```python
   NODE_REGISTRY = {
       "Planner": planner_node,
       "Searcher": searcher_node,
       "Reader": reader_node,
       "Compliance": compliance_node,
       "Writer": writer_node,
       "Critic": critic_node,
   }
   ```

3. **Node wrappers** — thin adapters: `State → agent function → dict update`
   - `planner_node(state)` calls `planner_agent(state["question"])`, returns `{"queries": ...}`
   - `writer_node(state)` includes Reflexion logic — reads `episodic_memory` for accumulated lessons
   - `critic_node(state)` includes Reflexion logic — appends `Reflection` to `episodic_memory` on rejection
   - `human_review_node(state)` — uses `interrupt()` for HITL gate on sensitive questions

4. **`critic_router(state)`** — conditional edge function: `"writer"` or `"end"`

5. **`human_router(state)`** — conditional edge after human review

6. **`build_graph(team: list[str])`** — DYNAMIC graph builder:
   - Filters `TAXONOMY` by team
   - Separates pipeline-phase roles from loop-phase roles
   - Sorts each by `order`
   - Registers only the needed nodes from `NODE_REGISTRY`
   - Wires pipeline nodes in sequence: `START → p1 → p2 → ... → Writer`
   - Wires loop: `Writer → Critic → (conditional) → Writer | human_review | END`
   - Compiles with `MemorySaver()` checkpointer (needed for HITL `interrupt()`)

#### `backend/api.py`

FastAPI application. Streaming lives ONLY here.

- `POST /research` — accepts `{"question": str, "max_iterations": int}`, creates a run, returns `{"run_id": str}`
- `GET /research/{run_id}/stream` — SSE endpoint that calls `graph.stream()` and yields events per node
- `POST /research/{run_id}/approve` — accepts `{"decision": "y" | "reason text"}`, resumes the paused graph with `Command(resume=...)`
- Serves static files from `frontend/` directory

> SSE streaming is handled entirely by calling `graph.stream()` instead of `graph.invoke()`. The orchestrator, agents, and all other modules have zero awareness of streaming.

#### `backend/requirements.txt`
```
langgraph>=0.2.50
langchain-core>=0.3.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
fastapi>=0.115.0
uvicorn>=0.30.0
python-dotenv>=1.0.0
```

---

### Frontend

#### `frontend/index.html`
- Single page with:
  - Input field for the research question
  - Submit button
  - Agent timeline area (events appear here as SSE messages arrive)
  - Final answer display area
  - Human approval card (hidden by default, shown when HITL triggers)

#### `frontend/index.css`
- Dark theme, modern design
- Smooth animations for agent events appearing in the timeline
- Approval card styling

#### `frontend/index.js`
- On submit: `POST /research` to get `run_id`, then open `EventSource` on `/research/{run_id}/stream`
- Each SSE event appends to the timeline (agent name + output)
- On stream end: display final answer
- On HITL event: show approval card with Approve/Reject buttons
  - On click: `POST /research/{run_id}/approve` with decision

---

### Entry Point

#### `main.py`
- Imports the FastAPI app from `backend/api.py`
- Runs with `uvicorn`

---

## What Is NOT Included (by design)

- A2A / MessageBus / Message envelope code
- RACI matrix in the frontend
- Incentive scan in the frontend
- Episodic memory visualization in the frontend
- Taxonomy table in the frontend

These concepts live in the backend code. Students learn them by reading the source.

---

## Execution Checklist

- [ ] **Step 1**: Create project directory structure and `__init__.py` files
- [ ] **Step 2**: `backend/llm.py` — shared LLM wrapper
- [ ] **Step 3**: `backend/tools/search.py` — DuckDuckGo as LangChain tool
- [ ] **Step 4**: `backend/agents/planner.py`
- [ ] **Step 5**: `backend/agents/searcher.py`
- [ ] **Step 6**: `backend/agents/reader.py`
- [ ] **Step 7**: `backend/agents/writer.py`
- [ ] **Step 8**: `backend/agents/critic.py`
- [ ] **Step 9**: `backend/agents/compliance.py`
- [ ] **Step 10**: `backend/agents/reflector.py`
- [ ] **Step 11**: `backend/config/taxonomy.py`
- [ ] **Step 12**: `backend/config/team_selector.py`
- [ ] **Step 13**: `backend/config/raci.py`
- [ ] **Step 14**: `backend/evaluation/incentives.py`
- [ ] **Step 15**: `backend/evaluation/serialization.py`
- [ ] **Step 16**: `backend/orchestrator.py` — State, node wrappers, dynamic graph builder
- [ ] **Step 17**: `backend/api.py` — FastAPI + SSE + HITL endpoint
- [ ] **Step 18**: `backend/requirements.txt`
- [ ] **Step 19**: `frontend/index.html`
- [ ] **Step 20**: `frontend/index.css`
- [ ] **Step 21**: `frontend/index.js`
- [ ] **Step 22**: `main.py` — entry point
- [ ] **Step 23**: `README.md`
- [ ] **Step 24**: Install dependencies and test run
