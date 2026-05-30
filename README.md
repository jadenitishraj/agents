# Multi-Agent Research System

A modular multi-agent research system built with **LangGraph**, **FastAPI**, and a simple HTML/JS frontend.

Ask a question → AI agents collaborate in real-time → get a well-researched answer.

## Concepts Taught

| Concept | Where to find it |
|---------|-----------------|
| **Taxonomy** | `backend/config/taxonomy.py` |
| **Team Selection** | `backend/config/team_selector.py` |
| **RACI** | `backend/config/raci.py` |
| **Orchestration** | `backend/orchestrator.py` |
| **Incentives** | `backend/evaluation/incentives.py` |
| **Serialization** | `backend/evaluation/serialization.py` |
| **Reflexion** | `backend/agents/reflector.py` + `orchestrator.py` |
| **Human-in-the-Loop** | `backend/orchestrator.py` (interrupt) + `backend/api.py` (approve endpoint) |

## Project Structure

```
agents/
├── backend/
│   ├── agents/          # Pure agent functions (no framework coupling)
│   ├── tools/           # LangChain tools (DuckDuckGo search)
│   ├── config/          # Taxonomy, team selection, RACI
│   ├── evaluation/      # Incentive scanning, serialization
│   ├── orchestrator.py  # State + dynamic LangGraph builder
│   ├── llm.py           # Shared LLM wrapper
│   └── api.py           # FastAPI + SSE streaming
├── frontend/            # Simple HTML/CSS/JS
└── main.py              # Entry point
```

## Quick Start

1. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

2. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Run the server (Backend + Frontend):**
   ```bash
   .venv/bin/python main.py
   ```

4. **Open in browser:**
   ```
   http://localhost:8000/static/index.html
   ```

## Advanced Testing

### Live Ragas Integration Test
To manually run the Ragas AI-as-a-Judge test (which triggers the live RAG global database and grades the AI's generated answer using OpenAI), open a new terminal window in the project root and run:

```bash
.venv/bin/python -m backend.rag_v2.ragas_evaluation
```

## How It Works

1. You type a research question.
2. The **team selector** analyzes the question and picks which agents to activate.
3. The **orchestrator** dynamically builds a LangGraph — only the needed agents are wired.
4. Agents execute in sequence: Planner → Searcher → (Reader) → (Compliance) → Writer → Critic.
5. If the Critic rejects, the Writer rewrites using **Reflexion** (episodic memory of past failures).
6. For sensitive topics, a **Human-in-the-Loop** gate pauses the pipeline for your approval.
7. The final answer is streamed back to the frontend via SSE.