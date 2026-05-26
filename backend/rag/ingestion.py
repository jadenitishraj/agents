"""Hot-folder document ingestion for the standalone RAG package."""

from __future__ import annotations

import shutil
from pathlib import Path

from llama_index.core import SimpleDirectoryReader

from .folders import data_root, pending_files
from .models import Source


def load_local_sources() -> tuple[list[Source], list[Path]]:
    files = pending_files()
    if not files:
        return [], []
    documents = SimpleDirectoryReader(input_files=[str(path) for path in files]).load_data()
    sources: list[Source] = []
    for path, document in zip(files, documents):
        text = document.get_content()
        sources.append(
            {
                "title": path.name,
                "url": path.as_uri(),
                "snippet": text[:300],
                "content": text,
                "source_type": "local_document",
            }
        )
    return sources, files


def move_processed(files: list[Path]) -> None:
    processed = data_root() / "processed"
    for path in files:
        if path.exists():
            shutil.move(str(path), str(processed / path.name))
