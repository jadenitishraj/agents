"""In-memory corpus registry for the RAG search feature."""

from __future__ import annotations

from .models import IndexedCorpus

_corpora: dict[str, IndexedCorpus] = {}


def register(corpus_id: str, corpus: IndexedCorpus) -> None:
    _corpora[corpus_id] = corpus


def get(corpus_id: str) -> IndexedCorpus | None:
    return _corpora.get(corpus_id)


def list_ids() -> list[str]:
    return list(_corpora.keys())


def remove(corpus_id: str) -> None:
    _corpora.pop(corpus_id, None)
