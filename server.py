#!/usr/bin/env python3
"""
ContextKeep V1.0 - MCP Server
Exposes memory tools to IDEs (VS Code, Cursor, etc.)
"""

import asyncio
import sys
import json
import os
import argparse
from fastmcp import FastMCP
from core.memory_manager import memory_manager

# Initialize FastMCP
mcp = FastMCP("context-keep")


@mcp.tool()
async def store_memory(key: str, content: str, tags: str = "", title: str = "") -> str:
    """
    Store a new memory or update an existing one.

    Args:
        key: Unique identifier for the memory (e.g., "project_notes", "meeting_2023-10-27")
        content: The actual content of the memory.
        tags: Comma-separated list of tags (optional).
        title: Human-readable title (optional).
    """
    print(f"DEBUG: store_memory called for key='{key}'")
    try:
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        # Add edit history for updates
        existing = memory_manager.retrieve_memory(key)
        
        # Create timestamp
        from datetime import datetime
        timestamp = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # Append log to content
        # This matches the WebUI's logging format for consistency
        if existing:
            content = f"{content}\n\n---\n**{timestamp} | AI Update via MCP**"
        else:
            content = f"{content}\n\n---\n**{timestamp} | Created via MCP**"

        result = memory_manager.store_memory(key, content, tag_list, title)
        print(f"DEBUG: store_memory success for key='{key}'")
        return f"✅ Memory stored: '{result['title']}' (Key: {key}) ({result['chars']} chars)"
    except Exception as e:
        print(f"DEBUG: store_memory failed: {e}")
        raise


@mcp.tool()
async def retrieve_memory(key: str) -> str:
    """
    Retrieve a memory by its key.

    Args:
        key: The unique identifier of the memory.
    """
    print(f"DEBUG: retrieve_memory called for key='{key}'")
    try:
        result = memory_manager.retrieve_memory(key)
        if result:
            print(f"DEBUG: retrieve_memory found key='{key}'")
            return f"📦 Memory: {result.get('title', key)}\n🔑 Key: {result['key']}\n📅 Updated: {result['updated_at']}\n\n{result['content']}"
        print(f"DEBUG: retrieve_memory NOT found key='{key}'")
        return f"❌ Memory not found: '{key}'"
    except Exception as e:
        print(f"DEBUG: retrieve_memory failed: {e}")
        raise


@mcp.tool()
async def search_memories(query: str) -> str:
    """
    Search for memories by key, title, or content.

    Args:
        query: The search term.
    """
    print(f"DEBUG: search_memories called for query='{query}'")
    try:
        results = memory_manager.search_memories(query)
        if not results:
            print(f"DEBUG: search_memories found 0 results")
            return f"🔍 No memories found for '{query}'"

        print(f"DEBUG: search_memories found {len(results)} results")
        output = f"🔍 Found {len(results)} memories for '{query}':\n\n"
        for mem in results:
            title = mem.get("title", mem["key"])
            output += f"- **{title}** (Key: {mem['key']}) ({mem['updated_at'][:16]}): {mem['snippet']}\n"
        return output
    except Exception as e:
        print(f"DEBUG: search_memories failed: {e}")
        raise


@mcp.tool()
async def list_recent_memories() -> str:
    """List the 10 most recently updated memories."""
    print("DEBUG: list_recent_memories called")
    try:
        memories = memory_manager.list_memories()[:10]
        if not memories:
            print("DEBUG: list_recent_memories found 0 memories")
            return "📭 No memories found."

        print(f"DEBUG: list_recent_memories found {len(memories)} memories")
        output = "📚 Recent Memories:\n"
        for mem in memories:
            title = mem.get("title", mem["key"])
            output += f"- {title} (Key: {mem['key']}) - {mem['updated_at'][:16]}\n"
        return output
    except Exception as e:
        print(f"DEBUG: list_recent_memories failed: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ContextKeep V1.0 - MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for SSE transport (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=5100, help="Port for SSE transport (default: 5100)"
    )
    parser.add_argument(
        "--generate-config", action="store_true", help="Generate MCP configuration JSON"
    )

    args = parser.parse_args()

    if args.generate_config:
        config = {
            "mcpServers": {
                "context-keep": {
                    "command": "python",
                    "args": [os.path.abspath(__file__)],
                }
            }
        }
        print(json.dumps(config, indent=2))
    else:
        if args.transport == "sse":
            print(
                f"🚀 Starting MCP server with SSE transport on {args.host}:{args.port}"
            )
            mcp.run(transport="sse", host=args.host, port=args.port)
        else:
            print("🚀 Starting MCP server with stdio transport")
            mcp.run(transport="stdio")
