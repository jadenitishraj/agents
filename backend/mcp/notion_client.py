"""Notion MCP Client — connects to the official Notion MCP Server.

Uses stdio transport to spawn the Notion MCP server via npx and wraps 
the `API-post-search` tool for LangChain to use.
"""

from __future__ import annotations

import asyncio
import os
import threading
from dotenv import load_dotenv

from langchain_core.tools import tool
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

load_dotenv()


def _run_notion_mcp(coro):
    """Run an async MCP call from sync code safely."""
    result = [None]
    exc = [None]

    def _target():
        try:
            result[0] = asyncio.run(coro)
        except Exception as e:
            exc[0] = e

    t = threading.Thread(target=_target)
    t.start()
    t.join()
    if exc[0]:
        raise exc[0]
    return result[0]


import json

def _extract_text(data) -> list[str]:
    """Recursively extract all 'plain_text' values from a Notion JSON object."""
    texts = []
    if isinstance(data, dict):
        if "plain_text" in data:
            texts.append(data["plain_text"])
        for v in data.values():
            texts.extend(_extract_text(v))
    elif isinstance(data, list):
        for item in data:
            texts.extend(_extract_text(item))
    return texts

async def _search_notion_api(query: str) -> str:
    """Connect to Notion MCP, search pages, and fetch their contents."""
    print(f"\n[MCP CLIENT] Spawning Notion Server to search for: '{query}'...")
    
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@notionhq/notion-mcp-server"],
        env={**os.environ, "NOTION_API_KEY": os.getenv("NOTION_TOKEN", "")}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Step 1: Search for pages
            args = {}
            if query:
                args["query"] = query
                
            search_res = await session.call_tool("API-post-search", args)
            
            if not search_res or not search_res.content or not hasattr(search_res.content[0], "text"):
                return "No search results returned."
                
            try:
                data = json.loads(search_res.content[0].text)
            except json.JSONDecodeError:
                return f"Failed to parse search results: {search_res.content[0].text}"
                
            results = data.get("results", [])
            
            # Fallback scan: if no pages matched the search, or if the search returned empty,
            # we query recent pages and search inside their blocks.
            is_fallback = False
            if not results and query:
                print(f"[MCP CLIENT] No page found matching '{query}'. Performing fallback block-scan...")
                is_fallback = True
                fallback_res = await session.call_tool("API-post-search", {})
                if fallback_res and fallback_res.content and hasattr(fallback_res.content[0], "text"):
                    try:
                        fallback_data = json.loads(fallback_res.content[0].text)
                        results = fallback_data.get("results", [])
                    except Exception:
                        pass

            if not results:
                return f"No Notion pages found matching '{query}'."

            # Step 2: Fetch contents for matching pages
            final_output = []
            matched_content_found = False
            
            for page in results[:3]:
                title_list = _extract_text(page.get("properties", {}).get("title", {}))
                title = " ".join(title_list) if title_list else "Untitled"
                url = page.get("url", "No URL")
                page_id = page.get("id")
                
                if not page_id:
                    continue
                    
                print(f"[MCP CLIENT] Scanning blocks for page: {title}")
                blocks_res = await session.call_tool("API-get-block-children", {"block_id": page_id})
                if blocks_res and blocks_res.content and hasattr(blocks_res.content[0], "text"):
                    try:
                        block_data = json.loads(blocks_res.content[0].text)
                        page_matches = []
                        
                        for block in block_data.get("results", []):
                            block_text_list = _extract_text(block)
                            block_text = " ".join(block_text_list)
                            
                            # Only filter blocks if we are performing a fallback search inside other pages
                            if is_fallback and query and query.lower() not in block_text.lower():
                                continue
                                
                            page_matches.append(block_text)
                            matched_content_found = True
                            
                            # Fetch children (like toggle contents/quotes)
                            if block.get("has_children"):
                                child_res = await session.call_tool("API-get-block-children", {"block_id": block["id"]})
                                if child_res and child_res.content and hasattr(child_res.content[0], "text"):
                                    child_data = json.loads(child_res.content[0].text)
                                    child_texts = _extract_text(child_data.get("results", []))
                                    if child_texts:
                                        page_matches.append("    " + "\n    ".join(child_texts))
                                        
                        if page_matches:
                            final_output.append(f"--- PAGE: {title} ({url}) ---")
                            final_output.extend(page_matches)
                            
                    except Exception as e:
                        final_output.append(f"(Failed to parse page blocks: {str(e)})")
            
            # If we searched for a query but couldn't find any block containing it
            if query and not matched_content_found:
                page_titles = []
                for page in results[:5]:
                    title_list = _extract_text(page.get("properties", {}).get("title", {}))
                    title = " ".join(title_list) if title_list else "Untitled"
                    page_titles.append(f"- {title} ({page.get('url', 'No URL')})")
                
                titles_str = "\n".join(page_titles)
                return f"No block containing the keyword '{query}' was found inside recent Notion pages.\n\nHowever, I was able to successfully connect to your Notion workspace and find these pages:\n{titles_str}\n\nYou can query specific keywords (e.g. 'Rumi', 'Quotes') to see their contents."

            print(f"[MCP SERVER] Notion composite search & read complete.")
            return "\n\n".join(final_output)

@tool
def search_notion(query: str = "") -> str:
    """Search the user's Notion workspace for pages and databases using a query string, AND return the actual text contents of those pages.
    Use this to fetch actual quotes, notes, and text from Notion pages.
    """
    return _run_notion_mcp(_search_notion_api(query))
