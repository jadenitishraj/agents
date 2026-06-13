"""MCP Math Server — arithmetic tools served via FastMCP.

Exposes add, subtract, multiply, divide as MCP tools.
Students learn: this is a standalone MCP server that can run
independently or be connected to via the MCP client.
"""

from fastmcp import FastMCP

mcp = FastMCP("Math Server")


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    print(f"\n[MCP SERVER] Tool Executed: Computing {a} + {b}")
    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    print(f"\n[MCP SERVER] Tool Executed: Computing {a} - {b}")
    return a - b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    print(f"\n[MCP SERVER] Tool Executed: Computing {a} * {b}")
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b. Raises error if b is zero."""
    print(f"\n[MCP SERVER] Tool Executed: Computing {a} / {b}")
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b


if __name__ == "__main__":
    mcp.run()
