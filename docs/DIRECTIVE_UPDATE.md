# ContextKeep V2 Directive Update

Use this block to replace V1 memory directives that mention `list_all_memories` or `tags`.

## Memory System

You are connected to an MCP server named `context-keep` for long-term memory.

### Server Validation

At the start of a memory-sensitive session, call `get_contextkeep_info` and confirm:

- Version is `2.1.0`
- Schema version is `2`
- The WebUI and MCP server report the same `database_id`
- Docker installs use `/app/data/contextkeep.db`
- The tool list includes all V2.1 tools below

If the client still shows `list_all_memories`, it is using stale V1.x tool metadata or the wrong server.

### Core Tools

| Tool | Purpose |
|------|---------|
| `get_contextkeep_info` | Get server version, backend, schema version, migration status, and available tools |
| `list_categories` | Start here; list live categories with counts and descriptions |
| `list_memories` | List memories, optionally filtered by category |
| `retrieve_memory` | Retrieve a memory by exact key |
| `search_memories` | Full-text search, optionally scoped to a category |
| `store_memory` | Store/update a memory with category assignments |
| `list_recent_memories` | List recently updated memories |

### Management Tools

| Tool | Purpose |
|------|---------|
| `create_category` | Create a category when no current category fits |
| `update_category` | Rename/edit a category |
| `delete_category` | Delete an empty category or reassign memories |
| `merge_categories` | Merge one category into another |
| `update_categories` | Reassign categories on a memory |
| `delete_memory` | Permanently delete a memory by key |
| `get_memory_stats` | Get memory/category statistics |
| `export_memories` | Export all memories as JSON |
| `get_edit_history` | View memory edit history |

## Retrieval Protocol

1. Call `list_categories()` first.
2. Choose the most relevant category from the live category list.
3. Call `list_memories(category="Category Name", limit=50)`.
4. Call `retrieve_memory(key="Exact_Key")` for the full content.
5. If the category path is not enough, use `search_memories(query="...")`.

## Storage Protocol

1. Call `list_categories()` before storing.
2. Assign at least one category from the live category list.
3. Use multiple categories when appropriate.
4. If no current category fits, call `create_category()` before storing.
5. Never assume the starter categories still exist or still have their original names.
6. Do not create narrow one-off categories when a combination of existing categories fits.

## Removed V1 Concepts

- `list_all_memories` is removed in V2.
- `tags` are replaced by `categories`.
- Old tags are preserved as `legacy_tags` migration metadata only.

## Client Configuration Notes

Most HTTP MCP clients use:

```json
{
  "mcpServers": {
    "context-keep": {
      "url": "http://localhost:5100/mcp"
    }
  }
}
```

Antigravity IDE uses `serverURL`, not `url`:

```json
{
  "mcpServers": {
    "context-keep": {
      "serverURL": "http://localhost:5100/mcp"
    }
  }
}
```

Remove old SSH/stdin configs that launch a different `server.py`; they can write to a database the V2.1 WebUI cannot see.

## Deletion Safety

If asked to delete a memory, ask for explicit confirmation before calling `delete_memory`.

If asked to delete a non-empty category, reassign or merge its memories first.
