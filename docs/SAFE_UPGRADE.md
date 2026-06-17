# ContextKeep V2.1 Safe Upgrade Guide

ContextKeep V2.1 includes a conservative upgrade path for both bare-metal and Docker installs.

The upgrade rule is simple: **no verified backup, no upgrade**.

## What The Backup Verifies

Before the upgrade continues, the backup tools check:

- The backup archive can be opened and fully read.
- Every archived file matches its SHA256 checksum.
- SQLite databases pass `PRAGMA integrity_check`.
- V1 JSON memory files can be parsed.
- A restore command is written into the backup folder.

If any check fails, the upgrade stops before changing the install.

## Backup Files

Backups are written to `backups/` by default. Each backup includes:

- A normal folder copy for quick inspection.
- A `.zip` archive for moving or storing elsewhere.
- `manifest.json` with paths, sizes, hashes, backup mode, and checks.
- `RESTORE_INSTRUCTIONS.md` with the matching restore command.

The `backups/` folder is ignored by Git.

The `source`, `compose_file`, and similar path fields in `manifest.json` are
informational breadcrumbs from the machine that created the backup. Restore
commands do not depend on those original paths; they restore from the archived
`files/` or `docker_data/` contents.

## Bare-Metal Upgrade

From the V2.1 folder, run:

```bash
python scripts/upgrade_to_v2_1.py baremetal
```

To migrate a V1 JSON memory folder into the V2.1 SQLite database:

```bash
python scripts/upgrade_to_v2_1.py baremetal --v1-source /path/to/old/data/memories
```

If you intentionally want to rebuild an existing target database during migration, add:

```bash
--reset-target
```

The script will:

1. Back up the current install folder.
2. Verify the backup archive and data integrity.
3. Run the V1 migration check if `--v1-source` is provided.
4. Run the migration only after the check passes.
5. Compile the Python files.
6. Run the ContextKeep health check.

### Bare-Metal Restore

Stop the MCP server and WebUI first, then run:

```bash
python scripts/restore_contextkeep.py baremetal --backup backups/<backup-name>.zip --target-dir /path/to/contextkeep --confirm
```

Before restoring, the helper creates a `*.pre_restore_<timestamp>` safety copy of the current target folder.

## Docker Upgrade

From the V2.1 folder, run:

```bash
python scripts/upgrade_to_v2_1.py docker
```

The script will:

1. Back up the existing Docker data from `/app/data`.
2. Copy the compose file and `.env` when present.
3. Verify the backup archive and SQLite integrity.
4. Stop the current compose stack.
5. Rebuild and start the V2.1 one-container stack.
6. Run the Docker health check inside the container.

If your older deployment uses a different compose file, service name, or named volume, pass it explicitly:

```bash
python scripts/upgrade_to_v2_1.py docker --compose-file /path/to/docker-compose.yml --service <service-name>
```

or:

```bash
python scripts/upgrade_to_v2_1.py docker --volume <docker-volume-name>
```

### Docker Restore

Stop the ContextKeep container first, then restore the backup to the Docker volume:

```bash
python scripts/restore_contextkeep.py docker --backup backups/<backup-name>.zip --volume <docker-volume-name> --confirm
```

Then start the stack again:

```bash
docker compose up -d
```

## Updating From Older Versions

### From V1.x

Use `--v1-source` to point at the old `data/memories` folder. V2.1 imports JSON memories into SQLite, preserves old tags as `legacy_tags`, and assigns categories.

### From V2.0

V2.0 Docker deployments may have separate WebUI and MCP containers. V2.1 defaults to one container so both services share the same SQLite database. Before starting V2.1, use the Docker backup command and confirm the backup contains the database used by the WebUI.

### From Unknown Or Customized Installs

Run a backup only first:

```bash
python scripts/backup_contextkeep.py baremetal --install-dir /path/to/contextkeep
```

or:

```bash
python scripts/backup_contextkeep.py docker --volume <docker-volume-name>
```

Inspect `manifest.json` and `RESTORE_INSTRUCTIONS.md` before continuing.

## After Any Upgrade

Verify the MCP server and WebUI point at the same database:

1. Open WebUI `/api/info`.
2. Call MCP `get_contextkeep_info`.
3. Compare `version`, `schema_version`, `storage_path`, `database_id`, and memory count.

The version should be `2.1.0`, and WebUI plus MCP should report the same `database_id`.

## Auto-Update Caution

If you use container auto-update software, do not enable unattended ContextKeep updates until you have an external backup routine. V2.1's upgrade tools are designed to verify backups before an upgrade, but an unattended image replacement cannot ask you to confirm backup health.
