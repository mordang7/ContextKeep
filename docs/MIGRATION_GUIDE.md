# ContextKeep V1 to V2 Migration Guide

This guide migrates V1 JSON memories into the V2 SQLite database.

## 1. Keep V1 Safe

Do not delete your V1 `data/memories` folder. The migration reads that folder and writes to a new SQLite database.

Before running a real migration, create a verified backup:

```bash
python scripts/backup_contextkeep.py baremetal --install-dir /path/to/contextkeep
```

The backup archive is opened, checksummed, and checked for SQLite/JSON integrity before an upgrade should continue.

## 2. Check The Migration

The safest route is the upgrade wrapper:

```bash
python scripts/upgrade_to_v2_1.py baremetal --v1-source /path/to/old/data/memories
```

Manual migration is also available:

```bash
python migrate.py --source ../ContextKeep/data/memories --target ./data/contextkeep.db --check
```

The check validates:

- Source folder exists
- JSON files are present
- SQLite FTS5 is available
- Target database status

## 3. Run The Migration

```bash
python migrate.py --source ../ContextKeep/data/memories --target ./data/contextkeep.db --reset-target
```

`--reset-target` is required when rebuilding an existing V2 database. Without it, the tool refuses to import into a populated database.

Only use `--reset-target` after a verified backup exists.

## 4. Review Results

After migration, confirm:

- Imported count matches JSON file count
- Every memory has at least one category
- `legacy_tags` were preserved
- `docs/DIRECTIVE_UPDATE.md` was generated

## 5. Verify Server Identity

Start the WebUI and MCP server, then compare:

- WebUI `/api/info`
- MCP `get_contextkeep_info`

Both should report the same:

- `version`
- `schema_version`
- `database_id`
- `storage_path`
- memory count

If those values differ, WebUI and MCP are connected to different databases.

## 6. Update MCP Client Configs

Point clients at the V2.1 HTTP MCP endpoint:

```json
{
  "mcpServers": {
    "context-keep": {
      "url": "http://localhost:5100/mcp"
    }
  }
}
```

For Antigravity IDE, use `serverURL` instead of `url`:

```json
{
  "mcpServers": {
    "context-keep": {
      "serverURL": "http://localhost:5100/mcp"
    }
  }
}
```

Remove any old SSH/stdin config for the same server name. If a client still shows `list_all_memories`, clear its cached MCP schema and restart it.

## 7. Update Agent Directives

Replace V1 directives that reference `list_all_memories` or `tags` with the V2 category-first flow in `docs/DIRECTIVE_UPDATE.md`.

See `docs/CLIENT_CONFIGURATION.md` for client-specific troubleshooting.
