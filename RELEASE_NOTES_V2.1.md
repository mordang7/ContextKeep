# ContextKeep V2.1 Atlas

ContextKeep V2.1 Atlas is a major upgrade focused on safer long-term memory, better agent workflows, and reliable Docker deployments.

## Highlights

- SQLite storage with FTS5 full-text search.
- User-editable categories replace fixed tags.
- Memories can belong to multiple categories.
- WebUI category management: create, rename, merge, delete, and reassign.
- New category-first MCP workflow with 16 tools.
- `get_contextkeep_info` verifies version, storage path, database ID, tool list, and migration status.
- Docker now runs WebUI and MCP in one default service so both use the same SQLite database.
- Verified backup, restore, and upgrade scripts for bare-metal and Docker users.
- Public client guides for standard HTTP MCP, Antigravity, and SSE fallback.

## Upgrade Safety

V2.1 includes backup-first upgrade tooling:

```bash
python scripts/upgrade_to_v2_1.py baremetal
python scripts/upgrade_to_v2_1.py docker
```

The upgrade wrapper creates a backup before proceeding, verifies the backup archive, checks SQLite integrity, records SHA256 checksums, and prints the matching restore command.

For details, read:

- `docs/SAFE_UPGRADE.md`
- `docs/DOCKER_V2_1.md`
- `docs/UPGRADING_FROM_V1.md`

## Breaking Changes

- `list_all_memories` has been removed.
- `tags` are replaced by `categories`.
- Agents should use `list_categories`, `list_memories`, and then `retrieve_memory`.
- V1 tags are preserved only as `legacy_tags` migration metadata.

## Recommended MCP Flow

```text
list_categories -> list_memories -> retrieve_memory
```

Use `search_memories` for topic discovery, then retrieve the exact memory before relying on it.

## Docker Notes

The default compose file now uses one service named `contextkeep` and one shared `/app/data/contextkeep.db`.

Fresh install:

```bash
docker compose up -d --build
```

Existing Docker install:

```bash
python scripts/upgrade_to_v2_1.py docker
```

After upgrading, confirm WebUI `/api/info` and MCP `get_contextkeep_info` report the same `database_id`, `storage_path`, and memory count.

## Validation Summary

Before release, V2.1 was checked for:

- Python compile success.
- Bare-metal healthcheck success.
- Verified bare-metal backup creation.
- Bare-metal restore smoke test.
- Docker build success.
- Temporary isolated Docker stack healthcheck.
- Docker backup creation and ZIP verification.
- Docker restore into a second volume.
- Corrupt database fail-closed behavior.
- Public file scan for private IPs, local paths, SSH keys, and obvious secrets.

## Older Versions

Older releases remain available through GitHub release history and tags. V2.1 is recommended for new installs and upgrades.
