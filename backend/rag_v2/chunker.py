from llama_index.core.schema import Document
from llama_index.core.node_parser import (
    MarkdownNodeParser,
    HTMLNodeParser,
    SentenceSplitter,
    TokenTextSplitter,
    SemanticSplitterNodeParser
)
from .llm import get_llama_embed_model

def chunk_document(parsed_doc: dict) -> list[dict]:
    """Split a parsed document into chunks based on its strategy. Returns a list of dicts."""
    print("  → Splitting document into chunks...")
    strategy = parsed_doc["chunk_strategy"]
    
    if strategy == "markdown":
        splitter = MarkdownNodeParser()
    elif strategy == "html":
        splitter = HTMLNodeParser()
    elif strategy == "token":
        splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=50)
    elif strategy == "semantic":
        splitter = SemanticSplitterNodeParser(
            buffer_size=1, breakpoint_percentile_threshold=90, embed_model=get_llama_embed_model()
        )
    else:
        splitter = SentenceSplitter(chunk_size=768, chunk_overlap=80)
        
    # Wrap text in a LlamaIndex Document just to pass it to the splitter
    doc = Document(text=parsed_doc["text"], metadata=parsed_doc["metadata"])
    nodes = splitter.get_nodes_from_documents([doc])
    
    # Extract the raw chunk data into simple Python dictionaries
    chunks = []
    for n in nodes:
        chunks.append({
            "id": n.node_id,
            "text": n.text,
            "metadata": n.metadata
        })
        
    print(f"  → Created {len(chunks)} chunks.")
    return chunks
