"""Storage management for vector and graph backends."""

from __future__ import annotations

import os

import chromadb
from llama_index.core import StorageContext
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.vector_stores.chroma import ChromaVectorStore

from .models import Source, StorageBundle
from .runtime import collection_name, has_neo4j_credentials, rag_storage_root


def build_storage(question: str, sources: list[Source]) -> StorageBundle:
    name = collection_name(question, sources)
    persist_dir = rag_storage_root() / name
    chroma_dir = persist_dir / "chroma"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(name=name)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    if has_neo4j_credentials():
        graph_store = Neo4jGraphStore(
            username=os.getenv("NEO4J_USERNAME", ""),
            password=os.getenv("NEO4J_PASSWORD", ""),
            url=os.getenv("NEO4J_URI", ""),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
        )
        backend = "neo4j"
    else:
        graph_store = SimpleGraphStore()
        backend = "simple"
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        graph_store=graph_store,
    )
    return StorageBundle(persist_dir, name, backend, storage_context, vector_store, graph_store)


def persist_storage(bundle: StorageBundle) -> None:
    bundle.persist_dir.mkdir(parents=True, exist_ok=True)
    bundle.storage_context.persist(persist_dir=str(bundle.persist_dir))

