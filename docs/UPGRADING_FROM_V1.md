# Upgrading From ContextKeep V1.x To V2.1 Atlas

V2.1 is a clean major-version break from V1.x. It removes the scaling-heavy V1 directory listing flow and replaces tags with user-editable categories.

## What Changed

| V1.x | V2.1 |
|------|------|
| JSON files | SQLite database |
| `tags` | `categories` |
| `list_all_memories` | `list_categories` + `list_memories` |
| Embedded edit logs | `edit_history` table |
| Fixed tag text | User-editable category records |

## Removed Tool

`list_all_memories` is intentionally removed. Do not add a compatibility shim. Agents should use:

1. `list_categories()`
2. `list_memories(category="Relevant Category")`
3. `retrieve_memory(key="Exact_Key")`

## Category Rules

- Users own their taxonomy.
- Starter categories are only defaults.
- Memories can have more than one category.
- Agents should inspect the live category list before storing memories.
- Agents may create a category only when no current category fits.

## Migration

Use the safe upgrade wrapper first:

```bash
python scripts/upgrade_to_v2_1.py baremetal --v1-source /path/to/old/data/memories
```

This creates and verifies a backup before the migration runs.

Manual migration is also available:

```bash
python migrate.py --source ../ContextKeep/data/memories --target ./data/contextkeep.db --check
python migrate.py --source ../ContextKeep/data/memories --target ./data/contextkeep.db --reset-target
```

Old tags are preserved as `legacy_tags` metadata for audit purposes, but they are not used by V2 operations.

Only use `--reset-target` after a verified backup exists.

## Docker Note

V2.1 defaults to one Docker service running both WebUI and MCP against one mounted SQLite database. This avoids the V2.0 deployment mistake where two containers could silently use different `/app/data/contextkeep.db` files.

For Docker upgrades, use:

```bash
python scripts/upgrade_to_v2_1.py docker
```

If the existing deployment uses a custom service or volume, see `docs/SAFE_UPGRADE.md`.

## Client Cutover

After migration, update every MCP client to point at the V2.1 endpoint and remove old SSH/stdin entries.

Standard HTTP MCP clients:

```json
{
  "mcpServers": {
    "context-keep": {
      "url": "http://localhost:5100/mcp"
    }
  }
}
```

Antigravity IDE:

```json
{
  "mcpServers": {
    "context-keep": {
      "serverURL": "http://localhost:5100/mcp"
    }
  }
}
```

Antigravity uses `serverURL`, not `url`. If it shows the old V1.x tool list after the config is corrected, clear its cached MCP schema for `context-keep` and restart the IDE.

Always verify with `get_contextkeep_info` before storing new memories. The client and WebUI must agree on `database_id`, `storage_path`, and memory count.

## Directive Update

Use `docs/DIRECTIVE_UPDATE.md` as the copy-ready replacement block for agent directive files.

Use `docs/CLIENT_CONFIGURATION.md` for detailed client troubleshooting.
