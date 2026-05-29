import os
from pathlib import Path

from .parser import parse_file
from .chunker import chunk_document
from .indexer import index_chunks
from .retriever import search_global_db
from .llm import configure_settings

def ingest_file(file_path: str) -> dict:
    """
    The Upload Pipeline. 
    Completely isolated from searching. Takes a file, processes it, and saves it globally.
    """
    configure_settings()
    
    print(f"\n=== Starting Upload Pipeline for: {file_path} ===")
    
    # 1. Loader & Parser
    parsed_dict = parse_file(file_path)
    
    # 2. Chunker
    chunk_dicts = chunk_document(parsed_dict)
    
    # 3. Indexer (Saves to Global Vector, Graph, and BM25)
    index_chunks(chunk_dicts)
    
    return {
        "status": "success",
        "message": f"Successfully uploaded {file_path}",
        "file": file_path,
        "chunks_created": len(chunk_dicts)
    }

def search_rag(query: str, top_k: int = 3) -> dict:
    """
    The Search Pipeline.
    Completely isolated from uploading. Searches the global database.
    """
    configure_settings()
    
    # Simple direct call to the retriever
    results = search_global_db(query, top_k=top_k)
    return results
