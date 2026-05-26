"""Unified ingestion, vector indexing, and graph indexing."""

from __future__ import annotations

from llama_index.core import KnowledgeGraphIndex, VectorStoreIndex
from llama_index.core.ingestion import IngestionPipeline

from .classifier import classify_sources
from .ingestion import load_local_sources, move_processed
from .models import IndexedCorpus, Source
from .parser import parse_sources
from .llm import configure_settings, get_llama_embed_model, get_llama_llm
from .store import build_storage, persist_storage


def build_corpus(question: str, sources: list[Source]) -> IndexedCorpus:
    configure_settings()
    local_sources, local_files = load_local_sources()
    all_sources = sources + local_sources
    classified = classify_sources(all_sources)
    documents, nodes = parse_sources(classified)
    storage = build_storage(question, all_sources)
    pipeline = IngestionPipeline(transformations=[get_llama_embed_model()])
    processed_nodes = list(pipeline.run(nodes=nodes))
    vector_index = VectorStoreIndex(
        processed_nodes,
        embed_model=get_llama_embed_model(),
        storage_context=storage.storage_context,
        show_progress=False,
    )
    try:
        graph_index = KnowledgeGraphIndex.from_documents(
            documents,
            storage_context=storage.storage_context,
            llm=get_llama_llm(),
            max_triplets_per_chunk=2,
            include_embeddings=True,
            show_progress=False,
        )
    except Exception:
        graph_index = None
    persist_storage(storage)
    move_processed(local_files)
    return IndexedCorpus(question, all_sources, classified, documents, processed_nodes, storage, vector_index, graph_index)
