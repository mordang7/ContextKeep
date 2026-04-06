#!/usr/bin/env python3
"""
ContextKeep V1.3 "Harbor" - MCP Server
Exposes memory tools to IDEs (VS Code, Cursor, etc.)
"""

import asyncio
import sys
import json
import os
import argparse
from datetime import datetime
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


@mcp.tool()
async def list_all_memories() -> str:
    """
    List ALL stored memories as a complete directory — keys, titles, tags, and last-updated timestamps.

    Use this as your FIRST step when you need to find a specific memory but are unsure of the
    exact key. Pick the correct key from this list, then call retrieve_memory(key) directly.
    This avoids unreliable fuzzy search and ensures accurate retrieval in one extra call.
    """
    print("DEBUG: list_all_memories called")
    try:
        memories = memory_manager.list_memories()
        if not memories:
            print("DEBUG: list_all_memories found 0 memories")
            return "📭 No memories stored yet."

        print(f"DEBUG: list_all_memories found {len(memories)} memories")
        output = f"📚 Memory Directory — {len(memories)} total memories:\n"
        output += "=" * 50 + "\n\n"
        for mem in memories:
            title = mem.get("title", mem["key"])
            tags = ", ".join(mem.get("tags", [])) if mem.get("tags") else "none"
            updated = mem.get("updated_at", "")[:16]
            output += f"🔑 Key:     {mem['key']}\n"
            output += f"   Title:   {title}\n"
            output += f"   Tags:    {tags}\n"
            output += f"   Updated: {updated}\n\n"
        return output
    except Exception as e:
        print(f"DEBUG: list_all_memories failed: {e}")
        raise


@mcp.tool()
async def delete_memory(key: str) -> str:
    """
    Delete a memory by its key. This action is permanent and cannot be undone.

    Args:
        key: The unique identifier of the memory to delete.
    """
    print(f"DEBUG: delete_memory called for key='{key}'")
    try:
        success = memory_manager.delete_memory(key)
        if success:
            print(f"DEBUG: delete_memory success for key='{key}'")
            return f"🗑️ Memory deleted: '{key}'"
        print(f"DEBUG: delete_memory NOT found key='{key}'")
        return f"❌ Memory not found: '{key}'"
    except Exception as e:
        print(f"DEBUG: delete_memory failed: {e}")
        raise


@mcp.tool()
async def get_memory_stats() -> str:
    """Get statistics about the memory store — total count, total characters, and storage path."""
    print("DEBUG: get_memory_stats called")
    try:
        stats = memory_manager.get_stats()
        print(f"DEBUG: get_memory_stats returning {stats['total_count']} memories")
        return (
            f"📊 Memory Stats:\n"
            f"   Total memories: {stats['total_count']}\n"
            f"   Total characters: {stats['total_chars']:,}\n"
            f"   Storage path: {stats['storage_path']}"
        )
    except Exception as e:
        print(f"DEBUG: get_memory_stats failed: {e}")
        raise


@mcp.tool()
async def export_memories() -> str:
    """
    Export all memories as a JSON string. Use this for backup or migration.
    Returns the full content of every memory in a single JSON array.
    """
    print("DEBUG: export_memories called")
    try:
        memories = memory_manager.list_memories()
        # Remove snippets (they're computed, not stored)
        for mem in memories:
            mem.pop("snippet", None)
        print(f"DEBUG: export_memories exporting {len(memories)} memories")
        return json.dumps(memories, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"DEBUG: export_memories failed: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ContextKeep V1.3 Harbor - MCP Server")
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
                f"🚀 Starting ContextKeep V1.3 Harbor MCP server (SSE) on {args.host}:{args.port}"
            )
            mcp.run(transport="sse", host=args.host, port=args.port)
        else:
            print("🚀 Starting ContextKeep V1.3 Harbor MCP server (stdio)")
            mcp.run(transport="stdio")
