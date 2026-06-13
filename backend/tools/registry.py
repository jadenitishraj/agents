"""Central tool registry — single source of truth for all tools.

Agents receive tools from here, never import them directly.
"""

from backend.tools.search import search_web
from backend.rag_v2.retriever import search_global_db
from backend.mcp.client import mcp_add, mcp_subtract, mcp_multiply, mcp_divide

TOOL_REGISTRY = {
    "web_search": search_web,
    "global_db_search": search_global_db,
    "mcp_add": mcp_add,
    "mcp_subtract": mcp_subtract,
    "mcp_multiply": mcp_multiply,
    "mcp_divide": mcp_divide,
}
