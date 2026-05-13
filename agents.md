# Multi-Agent Research System — Project Context

> **Read this file first.** It gives full project context without needing to scan source files.

## Purpose

A modular multi-agent research system for teaching students how to build production-grade AI orchestration. A user asks a question via a web frontend, agents collaborate (plan → search → read → comply → write → critique), and a final answer is returned.

## Tech Stack

| Layer | Tech |
|-------|------|
| Orchestration | LangGraph (StateGraph, dynamic wiring) |
| LLM | langchain-openai (ChatOpenAI, gpt-4o-mini) |
| Tools | langchain-community (DuckDuckGoSearchResults) |
| Observability | LangSmith (@traceable, auto-tracing) |
| API | FastAPI (single POST endpoint) |
| Frontend | Vanilla HTML/CSS/JS (no framework) |
| Environment | python-dotenv (.env file) |

## Directory Structure

```
agents/
├── agents.md                          # THIS FILE — project context for AI sessions
├── main.py                            # Entry point — starts uvicorn server
├── README.md                          # Quick start guide for students
├── .env                               # API keys (OPENAI_API_KEY, LANGSMITH_API_KEY)
├── .gitignore                         # Excludes __pycache__, .env, .DS_Store
│
├── backend/
│   ├── __init__.py
│   ├── llm.py                         # Shared ChatOpenAI wrapper (get_llm, call_llm)
│   ├── orchestrator.py                # State TypedDict + node wrappers + dynamic graph builder
│   ├── api.py                         # FastAPI app — single POST /research endpoint
│   ├── requirements.txt               # Python dependencies
│   │
│   ├── agents/                        # Pure functions — no LangGraph awareness
│   │   ├── __init__.py
│   │   ├── planner.py                 # question → list[queries]
│   │   ├── searcher.py                # queries → list[sources] (uses DuckDuckGo tool)
│   │   ├── reader.py                  # question + sources → list[facts]
│   │   ├── writer.py                  # question + sources + facts + feedback → answer
│   │   ├── critic.py                  # question + answer + sources → (approved, issues)
│   │   ├── compliance.py              # question → disclaimer (for sensitive topics)
│   │   └── reflector.py               # critic issues → Reflection dataclass (Reflexion pattern)
│   │
│   ├── tools/                         # LangChain tools (not agents)
│   │   ├── __init__.py
│   │   └── search.py                  # DuckDuckGo wrapped as search_web() function
│   │
│   ├── config/                        # Pure data and selection logic
│   │   ├── __init__.py
│   │   ├── taxonomy.py                # TAXONOMY dict with phase/order metadata
│   │   ├── team_selector.py           # select_team(), needs_deep_reading(), is_sensitive()
│   │   └── raci.py                    # RACIEntry dataclass, build_raci()
│   │
│   └── evaluation/                    # Post-run analysis
│       ├── __init__.py
│       ├── incentives.py              # IncentiveRisk dataclass, scan_incentives()
│       └── serialization.py           # serialize_trace(), deserialize_trace()
│
├── frontend/
│   ├── index.html                     # Single page: input → spinner → answer
│   ├── index.css                      # Dark theme, Inter font, accent glows
│   └── index.js                       # One fetch() call to POST /research
│
└── plans/                             # Feature plans with checklists
    └── TEMPLATE.md                    # Standard template for new feature plans
```

## Architecture

```
User Question
     │
     ▼
 POST /research (api.py)
     │
     ▼
 create_initial_state() ──► select_team() ──► build_raci()
     │
     ▼
 compile_graph(team) ──► build_graph(team)
     │                      │
     │          Reads TAXONOMY phase/order
     │          Wires ONLY active nodes
     │
     ▼
 graph.invoke(state)
     │
     ├─► planner_node ──► planner_agent() ──► call_llm()
     ├─► searcher_node ──► searcher_agent() ──► search_web() [DuckDuckGo tool]
     ├─► reader_node (conditional) ──► reader_agent() ──► call_llm()
     ├─► compliance_node (conditional) ──► compliance_agent() ──► call_llm()
     ├─► writer_node ──► writer_agent() ──► call_llm()
     └─► critic_node ──► critic_agent() ──► call_llm()
           │
           ├─ APPROVED ──► human_review_node (auto-approves after 3s) ──► END
           └─ REJECTED ──► reflector_agent() ──► append to episodic_memory ──► writer_node (loop)
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **No A2A / MessageBus** | LangGraph's native State management is sufficient for a unified Python backend |
| **Agents are pure functions** | No framework coupling. Easy to test. Students read clean input→output code |
| **Dynamic graph building** | Graph shape changes based on team. If Reader isn't needed, no Reader node exists |
| **HITL auto-approves (3s)** | Concept is visible in code but doesn't block execution. Students learn by reading, not by interacting |
| **No SSE streaming** | Keeps frontend simple — one fetch() call. Students don't need to learn EventSource |
| **DuckDuckGo as LangChain tool** | The Searcher is the agent; DuckDuckGo is the tool. Swappable without touching agent code |
| **Reflexion via episodic_memory** | Lessons are appended (list), not overwritten. Writer reads accumulated lessons on rewrites |

## API Contract

### `POST /research`

**Request:**
```json
{"question": "What is Python?", "max_iterations": 3}
```

**Response:**
```json
{
  "question": "What is Python?",
  "team": ["Planner", "Searcher", "Writer", "Critic"],
  "final_answer": "Python is a high-level...",
  "iterations": 1,
  "llm_calls": 3,
  "sources_count": 15,
  "duration_seconds": 16.3,
  "was_sensitive": false
}
```

## State Schema (orchestrator.py)

| Field | Type | Purpose |
|-------|------|---------|
| `question` | str | The research question |
| `team` | list[str] | Active agent roles |
| `queries` | list[str] | Planner output — search queries |
| `sources` | list[dict] | Searcher output — {title, url, snippet} |
| `facts` | list[str] | Reader output — extracted facts |
| `disclaimer` | str | Compliance output — one-sentence warning |
| `answer` | str | Writer output — the current draft |
| `critic_feedback` | str | Critic issues joined as string |
| `approved` | bool | Critic verdict |
| `issues` | list[str] | Critic's specific objections |
| `iterations` | int | How many writer-critic loops so far |
| `max_iterations` | int | Loop limit (default 3) |
| `sources_count` | int | Number of deduplicated sources |
| `llm_calls` | int | Total LLM invocations |
| `duration_seconds` | float | Total pipeline time |
| `was_sensitive` | bool | Whether sensitive keywords were detected |
| `critic_first_pass` | bool | True if approved on iteration 1 |
| `final_answer` | str | Copy of answer after completion |
| `episodic_memory` | list[Reflection] | Reflexion lessons from past iterations |

## TAXONOMY Metadata (config/taxonomy.py)

Each role has `phase` and `order` for dynamic graph wiring:

| Role | always | phase | order |
|------|--------|-------|-------|
| Planner | ✅ | pipeline | 1 |
| Searcher | ✅ | pipeline | 2 |
| Reader | ❌ | pipeline | 3 |
| Compliance | ❌ | pipeline | 4 |
| Writer | ✅ | loop | 1 |
| Critic | ✅ | loop | 2 |

## Environment Variables (.env)

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for ChatOpenAI |
| `LLM_MODEL` | Model name (default: gpt-4o-mini) |
| `LLM_TEMPERATURE` | Temperature (default: 0.3) |
| `LANGSMITH_TRACING` | Enable tracing (true/false) |
| `LANGSMITH_ENDPOINT` | LangSmith API URL |
| `LANGSMITH_API_KEY` | LangSmith API key |
| `LANGSMITH_PROJECT` | LangSmith project name |

## Concepts Taught (for students)

| Concept | File(s) | What students learn |
|---------|---------|--------------------|
| Taxonomy | config/taxonomy.py | Role classification with mission, phase, order |
| Team Selection | config/team_selector.py | Dynamic team composition based on question analysis |
| RACI | config/raci.py | Responsibility assignment matrix |
| Dynamic Orchestration | orchestrator.py | Graph shape changes per question — no hardcoded nodes |
| Reflexion | agents/reflector.py + orchestrator.py | Episodic memory — lessons from past failures |
| Incentive Scanning | evaluation/incentives.py | Detecting behavioral drift (speed-over-depth, rubber-stamping) |
| Serialization | evaluation/serialization.py | State crossing boundaries with schema versioning |
| HITL | orchestrator.py (human_review_node) | Human-in-the-loop concept (auto-approved for simplicity) |
| Tool vs Agent | tools/search.py + agents/searcher.py | DuckDuckGo is a tool, Searcher is the agent that uses it |
| Observability | All agents (@traceable) + api.py | LangSmith tracing for every agent, tool, and LLM call |

## How to Run

```bash
# 1. Set API keys in .env
# 2. Install dependencies
pip install -r backend/requirements.txt
# 3. Start server
python main.py
# 4. Open browser
open http://localhost:8000/static/index.html
```
