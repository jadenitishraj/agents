import os
from pathlib import Path

def determine_strategy(text: str, ext: str) -> str:
    """Decide the chunking strategy based on file extension and content heuristics."""
    if ext == ".md":
        return "markdown"
    if ext in (".html", ".htm"):
        return "html"
    if ext in (".log", ".trace", ".json", ".py"):
        return "token"
        
    # Table heavy heuristic
    if text.count("|") > 20 and text.count("\n") > 5:
        return "markdown"
        
    # YouTube script / No grammar heuristic
    # (Lots of text but very few periods or commas)
    word_count = len(text.split())
    punctuation_count = text.count(".") + text.count(",") + text.count("!") + text.count("?")
    if word_count > 50 and punctuation_count < (word_count * 0.05):
        return "token"
        
    return "semantic"

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
    
    # Determine classification using heuristic function
    strategy = determine_strategy(text, ext)
        
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
