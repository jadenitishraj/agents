"""Indexer — build all 3 search indexes from chunked documents.

After the chunker splits documents into nodes, the indexer makes them
searchable by building three different indexes:

1. Vector Index (ChromaDB) — semantic search using embeddings
   Best for: "find chunks that mean the same thing as my question"

2. BM25 Index — keyword search using term frequency
   Best for: "find chunks that contain the exact words in my question"

3. Knowledge Graph Index — entity-relationship triplet extraction
   Best for: "find chunks connected through entity relationships"

All three are stored so the retriever can query them without rebuilding.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from llama_index.core import KnowledgeGraphIndex, StorageContext, VectorStoreIndex
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.core.ingestion import IngestionPipeline
from llama_index.vector_stores.chroma import ChromaVectorStore

from .llm import get_llama_embed_model, get_llama_llm
from .models import IndexedCorpus, Source, StorageBundle

load_dotenv()

_ROOT = Path(__file__).resolve().parent


# ─── Storage path helpers ────────────────────────────────────
# Each corpus gets its own directory under .storage/ to keep
# ChromaDB collections and graph data isolated per question.

def _storage_root() -> Path:
    """Return the root directory for all persisted indexes."""
    root = Path(os.getenv("RAG_PERSIST_DIR", _ROOT / ".storage"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _collection_name(question: str, sources: list[Source]) -> str:
    """Generate a unique, human-readable collection name from the question + sources."""
    seed = question + "|" + "|".join(s.get("url", "") for s in sources)
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", question.lower()).strip("-")[:36]
    return f"{slug or 'rag'}-{digest}"


# ─── Storage context setup ───────────────────────────────────
# Creates ChromaDB vector store + graph store (SimpleGraphStore
# which saves to a local JSON file).

def _build_storage(question: str, sources: list[Source]) -> StorageBundle:
    """Set up ChromaDB + graph store and return a StorageBundle."""
    name = _collection_name(question, sources)
    persist_dir = _storage_root() / name
    chroma_dir = persist_dir / "chroma"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    # ChromaDB: embedded vector database — no server needed.
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(name=name)
    vector_store = ChromaVectorStore(chroma_collection=collection)

    # Graph store: SimpleGraphStore which saves to a local JSON file.
    graph_store = SimpleGraphStore()
    backend = "simple"

    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        graph_store=graph_store,
    )
    return StorageBundle(persist_dir, name, backend, storage_context, vector_store, graph_store)


def _persist(bundle: StorageBundle) -> None:
    """Save the storage context to disk so indexes survive server restarts."""
    bundle.persist_dir.mkdir(parents=True, exist_ok=True)
    bundle.storage_context.persist(persist_dir=str(bundle.persist_dir))


# ─── Build all 3 indexes ────────────────────────────────────

def build_indexes(
    question: str,
    sources: list[Source],
    documents: list,
    nodes: list,
) -> tuple[StorageBundle, VectorStoreIndex, object | None, list]:
    """Build vector, BM25, and knowledge graph indexes from chunked nodes.

    Returns (storage_bundle, vector_index, graph_index, processed_nodes).
    """
    print("Building 3 indexes (Vector, BM25 context, Graph) from chunks...")
    storage = _build_storage(question, sources)

    # 1. Embedding pipeline: convert text chunks → vectors via OpenAI embeddings.
    print("  → Generating embeddings for Vector index...")
    pipeline = IngestionPipeline(transformations=[get_llama_embed_model()])
    processed_nodes = list(pipeline.run(nodes=nodes))

    # 2. Vector index: store embedded nodes in ChromaDB for semantic search.
    # IMPORTANT: As a side effect, VectorStoreIndex also saves the raw text of every
    # chunk (the processed_nodes) into a local file called `docstore.json` inside your storage folder.
    # BM25 Keyword search REQUIRES this docstore.json file later to rebuild its word frequencies!
    vector_index = VectorStoreIndex(
        processed_nodes,
        embed_model=get_llama_embed_model(),
        storage_context=storage.storage_context,
        show_progress=False,
    )

    # 3. Knowledge graph index: extract entity-relationship triplets from documents.
    # max_triplets_per_chunk=2 keeps it fast (fewer LLM calls per chunk).
    # Falls back to None if triplet extraction fails (e.g., bad doc format).
    print("  → Extracting entity triplets for Knowledge Graph index...")
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

    # 4. Save everything to the hard drive!
    # This writes:
    #   - chroma/            (Vector Index)
    #   - graph_store.json   (Graph Index)
    #   - docstore.json      (The raw text nodes needed by BM25!)
    _persist(storage)
    return storage, vector_index, graph_index, processed_nodes
