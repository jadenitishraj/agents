import json
from pathlib import Path
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.schema import TextNode
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.core import KnowledgeGraphIndex
from .llm import get_llama_embed_model, get_llama_llm

GLOBAL_STORAGE_DIR = Path(__file__).resolve().parent / ".global_storage"

def get_global_storage():
    """Returns the StorageContext pointing to our permanent global database."""
    GLOBAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    chroma_dir = GLOBAL_STORAGE_DIR / "chroma"
    chroma_dir.mkdir(exist_ok=True)
    
    # 1. ChromaDB global collection
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(name="global_knowledge")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    
    # 2. SimpleGraphStore global file
    graph_store = SimpleGraphStore()
    graph_path = GLOBAL_STORAGE_DIR / "graph_store.json"
    if graph_path.exists():
        graph_store = SimpleGraphStore.from_persist_path(str(graph_path))
        
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        graph_store=graph_store
    )
    return storage_context

def _append_to_bm25_file(chunks: list[dict]):
    """Appends raw text chunks to a physical bm25_index.json file on disk."""
    bm25_path = GLOBAL_STORAGE_DIR / "bm25_index.json"
    existing = []
    
    if bm25_path.exists():
        with open(bm25_path, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                pass
                
    # Add new chunks to the global list
    existing.extend(chunks)
    
    with open(bm25_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

def index_chunks(chunks: list[dict]):
    """Embed chunks and save them to the global vector, graph, and BM25 databases."""
    print(f"Indexing {len(chunks)} chunks into global database...")
    storage = get_global_storage()
    
    # Convert dicts back to TextNode so LlamaIndex can process them
    nodes = [TextNode(id_=c["id"], text=c["text"], metadata=c["metadata"]) for c in chunks]
    
    # 1. Save to Global Vector Index (ChromaDB)
    print("  → Updating global Vector DB...")
    vector_index = VectorStoreIndex(
        nodes, 
        embed_model=get_llama_embed_model(),
        storage_context=storage,
        show_progress=False
    )
    
    # 2. Save to Global Graph Index (SimpleGraphStore)
    print("  → Updating global Graph DB...")
    try:
        graph_index = KnowledgeGraphIndex(
            nodes,
            storage_context=storage,
            llm=get_llama_llm(),
            max_triplets_per_chunk=2, #range is 5 to 15
            include_embeddings=True,
            show_progress=False
        )
    except Exception as e:
        print(f"Graph extraction failed (skipping): {e}")
        
    # 3. Persist the LlamaIndex databases to disk
    storage.persist(persist_dir=str(GLOBAL_STORAGE_DIR))
    
    # 4. Save to explicit BM25 JSON file
    print("  → Updating global BM25 file (bm25_index.json)...")
    _append_to_bm25_file(chunks)
    print("Indexing complete! Data is now permanently in the global DB.")
