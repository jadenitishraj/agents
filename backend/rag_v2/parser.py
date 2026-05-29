import os
from pathlib import Path

def parse_file(file_path: str) -> dict:
    """Read a file and classify its content type for chunking. Returns a simple dict."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File {file_path} not found.")
    
    print(f"  → Parsing file: {path.name}...")
    ext = path.suffix.lower()
    
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
        except Exception as e:
            print(f"  → Error parsing PDF: {e}")
            text = f"Error parsing PDF: {e}"
    else:
        text = path.read_text(encoding="utf-8", errors="replace")
    
    # Simple classification heuristic based on extension
    strategy = "sentence" # Default strategy
    
    if ext == ".md":
        strategy = "markdown"
    elif ext in (".html", ".htm"):
        strategy = "html"
    elif ext in (".log", ".trace", ".json", ".py"):
        strategy = "token"
        
    print(f"  → Classified as: {strategy} strategy")
    
    return {
        "title": path.name,
        "text": text,
        "chunk_strategy": strategy,
        "metadata": {
            "source_file": path.name,
            "extension": ext
        }
    }
