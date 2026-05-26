"""Hot-folder paths for local RAG documents."""

from __future__ import annotations

import os
from pathlib import Path

from .runtime import ROOT

SUPPORTED_SUFFIXES = {".md", ".pdf", ".txt"}


def data_root() -> Path:
    root = Path(os.getenv("RAG_DATA_DIR", ROOT / "data"))
    (root / "need-processing").mkdir(parents=True, exist_ok=True)
    (root / "processed").mkdir(parents=True, exist_ok=True)
    return root


def pending_files() -> list[Path]:
    pending = data_root() / "need-processing"
    return sorted(
        path for path in pending.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )

