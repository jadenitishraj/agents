"""MCP Client — connects to the Math Server and wraps tools as LangChain tools.

Uses in-process transport (no subprocess) by importing the FastMCP
server object directly. Each LangChain tool calls the MCP server
through the client protocol, proving the MCP round-trip works.
"""

from __future__ import annotations

import asyncio
import threading

from fastmcp import Client
from langchain_core.tools import tool

from backend.mcp.server import mcp as math_server


def _run_mcp(coro):
    """Run an async MCP call from sync code (safe inside event loops)."""
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


async def _call_tool(name: str, args: dict) -> str:
    """Open an in-process MCP session, call one tool, return text."""
    print(f"\n[MCP CLIENT] Opening session with Math Server to execute '{name}' tool...")
    async with Client(math_server) as client:
        result = await client.call_tool(name, args)
        if result.content and hasattr(result.content[0], "text"):
            return result.content[0].text
        return str(result)


# ── LangChain tool wrappers ─────────────────────────────────

@tool
def mcp_add(a: float, b: float) -> str:
    """Add two numbers using the MCP Math Server."""
    return _run_mcp(_call_tool("add", {"a": a, "b": b}))


@tool
def mcp_subtract(a: float, b: float) -> str:
    """Subtract b from a using the MCP Math Server."""
    return _run_mcp(_call_tool("subtract", {"a": a, "b": b}))


@tool
def mcp_multiply(a: float, b: float) -> str:
    """Multiply two numbers using the MCP Math Server."""
    return _run_mcp(_call_tool("multiply", {"a": a, "b": b}))


@tool
def mcp_divide(a: float, b: float) -> str:
    """Divide a by b using the MCP Math Server."""
    return _run_mcp(_call_tool("divide", {"a": a, "b": b}))


# All MCP math tools for easy import.
MCP_MATH_TOOLS = [mcp_add, mcp_subtract, mcp_multiply, mcp_divide]
