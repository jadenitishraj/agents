"""Shared LLM wrapper.

One place to set the model, temperature, and token limits.
Every agent reuses this — no direct OpenAI calls anywhere else.

Helicone Integration
--------------------
When HELICONE_ENABLED=true, requests are routed through Helicone's proxy
(oai.helicone.ai/v1) which logs cost, latency, and usage — without changing
OpenAI behaviour.  Per-agent custom properties let you filter the Helicone
dashboard by agent role (Planner, Writer, Critic, etc.).

When HELICONE_ENABLED=false (or HELICONE_API_KEY is missing), requests go
directly to OpenAI as before.  LangSmith tracing is unaffected either way.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

# ── Helicone configuration ───────────────────────────────────

HELICONE_API_KEY = os.getenv("HELICONE_API_KEY", "")
HELICONE_ENABLED = (
    os.getenv("HELICONE_ENABLED", "true").lower() == "true"
    and bool(HELICONE_API_KEY)
)

_llm: ChatOpenAI | None = None


def _build_helicone_headers(agent_name: str = "") -> dict[str, str]:
    """Build Helicone-specific headers for a request."""
    headers: dict[str, str] = {
        "Helicone-Auth": f"Bearer {HELICONE_API_KEY}",
        "Helicone-Cache-Enabled": "true",
    }
    if agent_name:
        headers["Helicone-Property-Agent"] = agent_name
    return headers


def get_llm(agent_name: str = "") -> ChatOpenAI:
    """Build a ChatOpenAI client.

    When Helicone is enabled, routes through the proxy with custom headers.
    The ``agent_name`` is sent as a Helicone property so the dashboard can
    show cost-per-agent breakdowns.

    When ``agent_name`` is empty, a shared singleton is returned (backward
    compatible).  When ``agent_name`` is provided, a fresh instance is
    created with agent-specific headers — this is cheap since LangChain
    only builds a thin wrapper around the HTTP client.
    """
    global _llm

    if not HELICONE_ENABLED:
        # Direct OpenAI — same as before.
        if _llm is None:
            _llm = ChatOpenAI(
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            )
        return _llm

    # Helicone proxy path — per-agent headers require per-agent instances.
    if agent_name:
        return ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            base_url="https://oai.helicone.ai/v1",
            default_headers=_build_helicone_headers(agent_name),
        )

    # No agent name — use cached singleton with base Helicone headers.
    if _llm is None:
        _llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            base_url="https://oai.helicone.ai/v1",
            default_headers=_build_helicone_headers(),
        )
    return _llm


def call_llm(prompt: str, max_tokens: int = 500, agent_name: str = "") -> str:
    """Send a single user prompt and return the text reply.

    Same shape as the vanilla wrapper — one prompt in, one string out.
    Pass ``agent_name`` to tag the request in Helicone (e.g. "Planner").
    """
    llm = get_llm(agent_name=agent_name).bind(max_tokens=max_tokens)
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()
