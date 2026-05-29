"""Parser — load documents from disk and classify their content type.

Load → Classify: two steps in one file because you always classify
right after loading. You can't classify without loading first, and
there's no reason to load without classifying.

Classification decides which chunking strategy the chunker will use:
  html_page        → html splitter
  markdown_notes   → markdown splitter
  transcript       → semantic splitter (topic-aware)
  unstructured_logs → token splitter (fixed windows)
  reference_report → hierarchical splitter (multi-level)
  clean_text       → sentence splitter (default)
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from llama_index.core import SimpleDirectoryReader

from .models import ClassifiedSource, Source

# --- File types the RAG pipeline can process ---
SUPPORTED_SUFFIXES = {".md", ".pdf", ".txt"}

_ROOT = Path(__file__).resolve().parent


# ─── Hot-folder management ──────────────────────────────────
# The hot-folder pattern: drop a file into need-processing/,
# the pipeline picks it up, indexes it, then moves it to processed/.

def data_root() -> Path:
    """Return the data directory, creating subfolders if needed."""
    root = Path(os.getenv("RAG_DATA_DIR", _ROOT / "data"))
    (root / "need-processing").mkdir(parents=True, exist_ok=True)
    (root / "processed").mkdir(parents=True, exist_ok=True)
    return root


def pending_files() -> list[Path]:
    """List files in the need-processing/ folder that we can handle."""
    pending = data_root() / "need-processing"
    return sorted(
        path for path in pending.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )


# ─── Document loading ───────────────────────────────────────
# SimpleDirectoryReader handles PDF, TXT, MD parsing automatically.
# It returns LlamaIndex Document objects with the extracted text.

def load_local_sources() -> tuple[list[Source], list[Path]]:
    """Read files from the hot-folder and convert them to Source dicts."""
    print("Loading files from hot-folder...")
    files = pending_files()
    if not files:
        return [], []
    documents = SimpleDirectoryReader(input_files=[str(p) for p in files]).load_data()
    sources: list[Source] = []
    for path, document in zip(files, documents):
        text = document.get_content()
        sources.append({
            "title": path.name,
            "url": path.as_uri(),
            "snippet": text[:300],
            "content": text,
            "source_type": "local_document",
        })
    return sources, files


def move_processed(files: list[Path]) -> None:
    """Move files from need-processing/ to processed/ after indexing."""
    processed = data_root() / "processed"
    for path in files:
        if path.exists():
            shutil.move(str(path), str(processed / path.name))


# ─── Content classification ─────────────────────────────────
# Heuristic rules that look at the raw text and guess what kind
# of document it is. Each category maps to a chunking strategy
# that the chunker.py will use.

def _detect_kind(text: str) -> tuple[str, str]:
    """Detect document type → return (category, chunk_strategy)."""
    lowered = text.lower()
    # HTML pages have tags — use the HTML-aware splitter.
    if "<html" in lowered or "<div" in lowered:
        return "html_page", "html"
    # Markdown uses # headers and - bullets — split on headers.
    if "# " in text or "## " in text or "- " in text:
        return "markdown_notes", "markdown"
    # Transcripts have timestamps (12:34) or speaker labels.
    if re.search(r"\b\d{1,2}:\d{2}\b", text) or "speaker" in lowered:
        return "transcript", "semantic"
    # Logs contain error/warn/trace keywords — fixed token windows.
    if re.search(r"\b(error|warn|trace|stack|http)\b", lowered):
        return "unstructured_logs", "token"
    # Long documents (8+ lines, 180+ words) → hierarchical multi-level chunks.
    if len(text.splitlines()) > 8 and len(text.split()) > 180:
        return "reference_report", "hierarchical"
    # Default: clean prose — sentence-level splitting.
    return "clean_text", "sentence"


def classify_sources(sources: list[Source]) -> list[ClassifiedSource]:
    """Classify each source and tag it with the right chunking strategy."""
    print(f"Classifying {len(sources)} sources...")
    classified: list[ClassifiedSource] = []
    for source in sources:
        title = source.get("title", "").strip() or "Untitled Source"
        snippet = source.get("snippet", "").strip()
        text = source.get("content", "").strip() or f"{title}\n\n{snippet}"
        category, chunk_strategy = _detect_kind(text)
        print(f"  → Classified '{title}' as '{category}' (strategy: {chunk_strategy})")
        metadata = {
            "title": title,
            "url": source.get("url", ""),
            "category": category,
            "chunk_strategy": chunk_strategy,
            "source_type": source.get("source_type", "web_search"),
        }
        classified.append(
            ClassifiedSource(title, source.get("url", ""), text, category, chunk_strategy, metadata)
        )
    return classified
