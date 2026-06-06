from backend.tools.search import search_web
from backend.tools.rag_retriever import search_global_db

TOOL_REGISTRY = {
    "web_search": search_web,
    "global_db_search": search_global_db,
}
