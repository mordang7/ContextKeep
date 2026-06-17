# ContextKeep V2.1 Client Configuration

This guide covers MCP client configuration and the most common split-database troubleshooting checks.

## Primary Endpoint

Use the streamable HTTP endpoint when the client supports it:

```text
http://localhost:5100/mcp
```

For a remote Docker host, replace `localhost` with the host address:

```text
http://<host>:5100/mcp
```

The SSE endpoint is a fallback for clients that do not support streamable HTTP:

```text
http://<host>:5100/sse
```

## Standard MCP JSON

Most clients use the standard `url` key:

```json
{
  "mcpServers": {
    "context-keep": {
      "url": "http://localhost:5100/mcp"
    }
  }
}
```

Examples: Codex, Gemini CLI, OpenCode, and other clients that follow the standard MCP config format.

The repository includes `mcp_config.example.json` and `mcp_config.docker.example.json` for this setup.
You can also generate this config with:

```bash
python server.py --generate-config --config-kind http
```

## Antigravity IDE

Antigravity IDE uses `serverURL`, not `url`, for HTTP MCP servers:

```json
{
  "mcpServers": {
    "context-keep": {
      "serverURL": "http://localhost:5100/mcp"
    }
  }
}
```

The repository includes `mcp_config.antigravity.example.json` for this setup.
You can also generate this config with:

```bash
python server.py --generate-config --config-kind antigravity
```

If you use the standard `url` key in Antigravity, the server may fail to load and Antigravity may continue showing stale cached tools.

## SSE Fallback

Use `mcp_config.sse.example.json` only when a client does not support the primary streamable HTTP endpoint.

## Claude / Antigravity Notes

Do not keep an old SSH/stdin server entry active for `context-keep`, especially one that launches `server.py` from an older checkout. That pattern can write to a legacy JSON or SQLite database that the V2.1 WebUI does not display.

## Verify Every Client

After adding ContextKeep to a client, call `get_contextkeep_info` before storing memories.

Expected V2.1 shape:

```json
{
  "name": "ContextKeep",
  "version": "2.1.0",
  "schema_version": "2",
  "storage_backend": "sqlite",
  "storage_path": "/app/data/contextkeep.db",
  "tools": [
    "store_memory",
    "retrieve_memory",
    "search_memories",
    "list_categories",
    "list_memories",
    "list_recent_memories",
    "delete_memory",
    "create_category",
    "update_category",
    "delete_category",
    "merge_categories",
    "update_categories",
    "get_memory_stats",
    "export_memories",
    "get_edit_history",
    "get_contextkeep_info"
  ]
}
```

The exact `database_id` is generated per database. Record it for your deployment and compare it across clients and the WebUI.

## Stale Tool List Troubleshooting

If a client shows `list_all_memories`, it is not using the current V2.1 tool schema.

Check these in order:

1. Confirm the config points to `http://<host>:5100/mcp`.
2. Confirm Antigravity uses `serverURL`, not `url`.
3. Remove any old SSH/stdin `context-keep` server entry.
4. Clear the client's cached MCP schema for `context-keep`.
5. Restart the client completely.
6. Call `get_contextkeep_info` again.

If a client caches MCP schemas, delete only the cached files for `context-keep`, then restart that client.

## Split-Database Symptoms

The server may be healthy while the client is pointed at the wrong database.

Signs:

- Agent says `store_memory` succeeded, but the WebUI does not show the memory.
- Agent reports an old tool list.
- Agent and WebUI show different memory counts.
- `get_contextkeep_info` reports a different `database_id` or `storage_path`.

Resolution:

1. Compare `get_contextkeep_info` from the client with WebUI `/api/info`.
2. Make sure both report the same `database_id`.
3. Make sure both report the same `storage_path`.
4. In Docker, keep WebUI and MCP in the default single `contextkeep` service unless you intentionally know how to share the exact same mounted database.

## Category Behavior

V2.1 uses categories instead of tags. Memories can belong to multiple categories.

Agents should:

1. Call `list_categories`.
2. Choose one or more existing categories when possible.
3. Create a category only when the memory represents a durable area that does not fit the live category list.
4. Use `update_categories` when only the category assignment changes.

The server can create missing categories when `store_memory` receives a new category name, but agent instructions should still prefer deliberate `list_categories` -> choose existing -> `create_category` only when needed.
