#!/usr/bin/env python3
"""ContextKeep V2.1 Atlas MCP server."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from fastmcp import FastMCP

from core.database import Database
from core.memory_manager import memory_manager


mcp = FastMCP("context-keep")


def _category_names(memory: dict[str, Any]) -> str:
    names = [category["name"] for category in memory.get("categories", [])]
    return ", ".join(names) if names else "Uncategorized"


def _memory_line(memory: dict[str, Any]) -> str:
    title = memory.get("title") or memory.get("key")
    updated = str(memory.get("updated_at", ""))[:19]
    categories = _category_names(memory)
    return f"- {title} (Key: {memory['key']}) [{categories}] - {updated}"


@mcp.tool()
async def store_memory(key: str, content: str, categories: str = "", title: str = "") -> str:
    """Store or update a memory with comma-separated category assignments."""
    memory = memory_manager.store_memory(key=key, content=content, categories=categories, title=title)
    return (
        f"Stored memory: {memory['title']}\n"
        f"Key: {memory['key']}\n"
        f"Categories: {_category_names(memory)}\n"
        f"Characters: {memory['chars']}"
    )


@mcp.tool()
async def retrieve_memory(key: str) -> str:
    """Retrieve a memory by exact key."""
    memory = memory_manager.retrieve_memory(key)
    if not memory:
        return f"Memory not found: {key}"
    history = memory.get("edit_history", [])[:5]
    history_text = "\n".join(
        f"- {item['timestamp']} | {item['action']} | {item['source']}"
        for item in history
    )
    if not history_text:
        history_text = "No edit history."
    return (
        f"Memory: {memory.get('title', key)}\n"
        f"Key: {memory['key']}\n"
        f"Updated: {memory['updated_at']}\n"
        f"Categories: {_category_names(memory)}\n\n"
        f"{memory['content']}\n\n"
        f"Edit History:\n{history_text}"
    )


@mcp.tool()
async def search_memories(query: str, category: str = "") -> str:
    """Full-text search memories, optionally scoped to a category."""
    results = memory_manager.search_memories(query, category or None, mask_credentials=True)
    scope = f" in {category}" if category else ""
    if not results:
        return f"No memories found for '{query}'{scope}."
    lines = [f"Found {len(results)} memories for '{query}'{scope}:"]
    for memory in results:
        snippet = memory.get("snippet") or ""
        lines.append(f"{_memory_line(memory)}\n  {snippet}")
    return "\n".join(lines)


@mcp.tool()
async def list_categories() -> str:
    """List live memory categories with counts and descriptions."""
    categories = memory_manager.list_categories()
    if not categories:
        return "No categories found."
    lines = [f"{len(categories)} categories:"]
    for category in categories:
        starter = "starter" if category.get("is_starter") else "custom"
        lines.append(
            f"- [{category['id']}] {category['icon']} {category['name']} "
            f"({category['memory_count']} memories, {starter}) - {category['description']}"
        )
    return "\n".join(lines)


@mcp.tool()
async def list_memories(category: str = "", limit: int = 50) -> str:
    """List memories, optionally filtered by category. V2 replacement for list_all_memories."""
    memories = memory_manager.list_memories(category or None, limit=limit, mask_credentials=True)
    scope = f" in {category}" if category else ""
    if not memories:
        return f"No memories found{scope}."
    lines = [f"{len(memories)} memories{scope}:"]
    lines.extend(_memory_line(memory) for memory in memories)
    return "\n".join(lines)


@mcp.tool()
async def list_recent_memories(limit: int = 10) -> str:
    """List recently updated memories."""
    memories = memory_manager.list_recent_memories(limit=limit)
    if not memories:
        return "No memories found."
    lines = [f"{len(memories)} recent memories:"]
    lines.extend(_memory_line(memory) for memory in memories)
    return "\n".join(lines)


@mcp.tool()
async def delete_memory(key: str) -> str:
    """Delete a memory permanently by key."""
    if memory_manager.delete_memory(key):
        return f"Deleted memory: {key}"
    return f"Memory not found: {key}"


@mcp.tool()
async def create_category(name: str, description: str = "", icon: str = "folder") -> str:
    """Create a new live category."""
    category = memory_manager.create_category(name, description, icon)
    return f"Created category [{category['id']}]: {category['name']}"


@mcp.tool()
async def update_category(
    category_id: int,
    name: str = "",
    description: str = "",
    icon: str = "",
) -> str:
    """Rename or edit category metadata by category id."""
    category = memory_manager.update_category(
        category_id,
        name=name or None,
        description=description or None,
        icon=icon or None,
    )
    return f"Updated category [{category['id']}]: {category['name']}"


@mcp.tool()
async def delete_category(category_id: int, reassign_to: int = 0) -> str:
    """Delete an empty category or reassign its memories to another category."""
    result = memory_manager.delete_category(category_id, reassign_to or None)
    deleted = result["deleted"]
    moved = result["reassigned_count"]
    if moved:
        return f"Deleted category '{deleted['name']}' and reassigned {moved} memories."
    return f"Deleted category '{deleted['name']}'."


@mcp.tool()
async def merge_categories(source_id: int, target_id: int) -> str:
    """Merge one category into another."""
    result = memory_manager.merge_categories(source_id, target_id)
    source = result["source"]["name"]
    target = result["target"]["name"]
    return f"Merged '{source}' into '{target}' ({result['moved_count']} memories touched)."


@mcp.tool()
async def update_categories(key: str, categories: str) -> str:
    """Reassign categories for an existing memory."""
    memory = memory_manager.update_categories(key, categories)
    return f"Updated categories for '{memory['title']}': {_category_names(memory)}"


@mcp.tool()
async def get_memory_stats() -> str:
    """Get memory and category statistics."""
    stats = memory_manager.get_stats()
    lines = [
        "Memory stats:",
        f"  Total memories: {stats['total_memories']}",
        f"  Total characters: {stats['total_chars']:,}",
        f"  Total categories: {stats['total_categories']}",
        f"  Storage path: {stats['storage_path']}",
        "  Categories:",
    ]
    for category in stats["per_category_counts"]:
        lines.append(f"    - {category['name']}: {category['memory_count']}")
    return "\n".join(lines)


@mcp.tool()
async def export_memories() -> str:
    """Export all memories as JSON, including categories and legacy tags."""
    return json.dumps(memory_manager.export_all(), indent=2, ensure_ascii=False)


@mcp.tool()
async def get_edit_history(key: str, limit: int = 10) -> str:
    """Get edit history for a memory."""
    history = memory_manager.get_edit_history(key, limit)
    if not history:
        return f"No edit history found for: {key}"
    lines = [f"Edit history for {key}:"]
    for item in history:
        lines.append(
            f"- {item['timestamp']} | {item['action']} | {item['source']} | "
            f"{json.dumps(item['details'], ensure_ascii=False)}"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_contextkeep_info() -> str:
    """Get ContextKeep version, backend, schema, tools, and migration status."""
    return json.dumps(memory_manager.get_contextkeep_info(), indent=2, ensure_ascii=False)


def build_config(kind: str = "http", host: str = "localhost", port: int = 5100) -> dict[str, Any]:
    if kind == "stdio":
        return {
            "mcpServers": {
                "context-keep": {
                    "command": "python",
                    "args": [os.path.abspath(__file__)],
                }
            }
        }

    endpoint = "sse" if kind == "sse" else "mcp"
    key = "serverURL" if kind == "antigravity" else "url"
    return {
        "mcpServers": {
            "context-keep": {
                key: f"http://{host}:{port}/{endpoint}",
            }
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="ContextKeep V2.1 Atlas MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse", "http"], default="stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5100)
    parser.add_argument("--generate-config", action="store_true")
    parser.add_argument(
        "--config-kind",
        choices=["http", "sse", "stdio", "antigravity"],
        default="http",
        help="Config shape to print with --generate-config.",
    )
    parser.add_argument(
        "--config-host",
        default="localhost",
        help="Host to use in generated HTTP/SSE client configs.",
    )
    args = parser.parse_args()

    if args.generate_config:
        print(json.dumps(build_config(args.config_kind, args.config_host, args.port), indent=2))
        return

    if args.transport in {"sse", "http"}:
        Database.verify_writable()
        info = memory_manager.get_contextkeep_info()
        print(
            "Starting ContextKeep V2.1 Atlas MCP server "
            f"({args.transport}) on {args.host}:{args.port}; "
            f"db={info['storage_path']}; database_id={info.get('database_id', '')}; "
            f"memories={info['migration_status']['memory_count']}",
            file=sys.stderr,
        )
        mcp.run(transport=args.transport, host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
