from __future__ import annotations

import os
from functools import lru_cache

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI as LlamaOpenAI


@lru_cache(maxsize=1)
def get_langchain_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
    )


@lru_cache(maxsize=1)
def get_langchain_embeddings() -> OpenAIEmbeddings:
    model = os.getenv("RAG_EMBED_MODEL", "text-embedding-3-small")
    return OpenAIEmbeddings(model=model)


@lru_cache(maxsize=1)
def get_llama_llm() -> LlamaOpenAI:
    return LlamaOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
    )


@lru_cache(maxsize=1)
def get_llama_embed_model() -> OpenAIEmbedding:
    model = os.getenv("RAG_EMBED_MODEL", "text-embedding-3-small")
    return OpenAIEmbedding(model=model)


def configure_settings() -> None:
    Settings.llm = get_llama_llm()
    Settings.embed_model = get_llama_embed_model()


def complete(prompt: str, max_tokens: int = 700) -> str:
    llm = get_langchain_llm().bind(max_tokens=max_tokens)
    return llm.invoke([HumanMessage(content=prompt)]).content.strip()
