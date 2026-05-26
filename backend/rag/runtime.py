"""Filesystem and environment helpers for the standalone RAG package."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv()


def rag_storage_root() -> Path:
    root = Path(os.getenv("RAG_PERSIST_DIR", ROOT / ".storage"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def collection_name(question: str, sources: list[dict[str, str]]) -> str:
    seed = question + "|" + "|".join(s.get("url", "") for s in sources)
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", question.lower()).strip("-")[:36]
    return f"{slug or 'rag'}-{digest}"


def has_neo4j_credentials() -> bool:
    keys = ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD")
    return all(os.getenv(key) for key in keys)
