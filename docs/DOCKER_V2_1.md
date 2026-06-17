# ContextKeep V2.1 Docker Deployment

V2.1 uses one Docker service for both WebUI and MCP by default.

This is deliberate. SQLite is reliable here, but users can accidentally create two different databases when WebUI and MCP are launched as separate containers with different volumes. One container, one mounted `/app/data`, and one `contextkeep.db` removes that failure mode for normal installs.

## Default Ports

| Service | URL |
|---------|-----|
| WebUI | `http://localhost:5000` |
| MCP HTTP | `http://localhost:5100/mcp` |

## Start

For an existing Docker install, prefer the safe upgrade wrapper:

```bash
python scripts/upgrade_to_v2_1.py docker
```

It creates and verifies a backup of the existing Docker data before rebuilding the V2.1 stack. If your older deployment uses a different compose file, service name, or volume, see `SAFE_UPGRADE.md` before continuing.

For a fresh Docker install:

```bash
docker compose up -d --build
```

## Verify

```bash
docker compose ps
docker compose logs contextkeep
docker compose exec contextkeep python scripts/healthcheck.py
```

The health check writes a tiny heartbeat to `schema_meta`, so a read-only database fails clearly instead of looking healthy.

## Shared Database Identity

V2.1 stores a stable `database_id` inside the SQLite database. WebUI `/api/info` and MCP `get_contextkeep_info` should show the same:

- `database_id`
- `storage_path`
- `migration_status.memory_count`

If those values differ, you are not talking to the same database.

In Docker, the expected storage path is:

```text
/app/data/contextkeep.db
```

For the default compose stack, MCP and WebUI should both report that path.

## Volume Name

The default volume name is `contextkeep_v2_data` so V2.1 can reuse data from an existing V2 test deployment.

Override it only when you intentionally want a separate install:

```bash
CONTEXTKEEP_VOLUME_NAME=contextkeep_v2_1_test_data docker compose up -d --build
```

Before changing a volume name, create a backup:

```bash
python scripts/backup_contextkeep.py docker --volume <docker-volume-name>
```

## Database Path

Inside Docker, both services use:

```text
/app/data/contextkeep.db
```

This is controlled with:

```text
CONTEXTKEEP_DB_PATH=/app/data/contextkeep.db
```

For local development, you can also set `CONTEXTKEEP_DATA_DIR` or `CONTEXTKEEP_DB_PATH` before running `server.py`, `webui.py`, or `migrate.py`.

## Client Configuration After Docker Starts

Most MCP clients use:

```json
{
  "mcpServers": {
    "context-keep": {
      "url": "http://localhost:5100/mcp"
    }
  }
}
```

The matching example file is `mcp_config.docker.example.json`.

Antigravity IDE uses `serverURL` instead:

```json
{
  "mcpServers": {
    "context-keep": {
      "serverURL": "http://localhost:5100/mcp"
    }
  }
}
```

The matching example file is `mcp_config.antigravity.example.json`.

If Antigravity shows old tools such as `list_all_memories`, clear its cached MCP schema for `context-keep` and restart the IDE. See `CLIENT_CONFIGURATION.md`.

## Split-Database Troubleshooting

If an agent can store and retrieve a memory but the WebUI does not show it:

1. Call `get_contextkeep_info` from the agent.
2. Open WebUI `/api/info`.
3. Compare `database_id`, `storage_path`, and memory count.
4. Remove old SSH/stdin MCP configs that launch a different `server.py`.
5. Use the default one-service compose stack unless you intentionally share the same mounted database between services.

## Rollback

Every safe upgrade backup includes `RESTORE_INSTRUCTIONS.md`. The Docker restore shape is:

```bash
python scripts/restore_contextkeep.py docker --backup backups/<backup-name>.zip --volume <docker-volume-name> --confirm
```

Stop the ContextKeep container before restoring, then start it again with `docker compose up -d`.
