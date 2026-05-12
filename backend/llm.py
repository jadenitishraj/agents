"""Shared LLM wrapper.

One place to set the model, temperature, and token limits.
Every agent reuses this — no direct OpenAI calls anywhere else.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

_llm: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI:
    """Lazily build a ChatOpenAI client. One instance shared across agents."""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
        )
    return _llm


def call_llm(prompt: str, max_tokens: int = 500) -> str:
    """Send a single user prompt and return the text reply.

    Same shape as the vanilla wrapper — one prompt in, one string out.
    """
    llm = get_llm().bind(max_tokens=max_tokens)
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()
