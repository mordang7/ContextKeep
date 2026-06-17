<div align="center">

![ContextKeep Banner](assets/banner.png)

# ContextKeep
### Long-Term Memory for AI Agents

[![Version: 2.1](https://img.shields.io/badge/Version-2.1-brightgreen?style=for-the-badge)](https://github.com/mordang7/ContextKeep)
[![Status: Stable](https://img.shields.io/badge/Status-Stable-blue?style=for-the-badge)](https://github.com/mordang7/ContextKeep)
[![Platform: Linux | Windows | macOS](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey?style=for-the-badge)](https://github.com/mordang7/ContextKeep)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge)](https://www.python.org/downloads/)
[![MCP Ready](https://img.shields.io/badge/MCP-Ready-green.svg?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/)

**ContextKeep** gives AI agents a persistent, searchable memory they can use across sessions. V2.1 adds SQLite, full-text search, user-editable categories, safer Docker defaults, and verified backup-first upgrades.

[What's New](#whats-new-in-v21-atlas) | [Safe Upgrade](#safe-upgrade-first) | [Install](#install) | [MCP Tools](#mcp-tools) | [Configuration](#mcp-client-configuration) | [Docs](#docs)

</div>

---

## Features

- Persistent local memory for MCP-compatible agents.
- SQLite storage with FTS5 full-text search.
- User-editable categories instead of fixed tags.
- Multiple categories per memory.
- WebUI for browsing, editing, searching, exporting, and category management.
- Streamable HTTP MCP endpoint at `/mcp`, with SSE fallback for older clients.
- Docker Compose support with one default service for WebUI and MCP.
- Verified backup and restore helpers for bare-metal and Docker upgrades.
- Server identity checks through `get_contextkeep_info`.

![ContextKeep Showcase](assets/Showcase.png)

## What's New In V2.1 Atlas

V2.1 is the first category-first ContextKeep release.

- `list_all_memories` has been removed.
- Agents now use `list_categories` and `list_memories` before `retrieve_memory`.
- `tags` are replaced by user-editable `categories`.
- Memories can belong to more than one category.
- V1 tags are preserved as `legacy_tags` migration metadata.
- Docker now runs WebUI and MCP together by default so both use the same SQLite database.
- `get_contextkeep_info` reports version, storage path, database ID, tool list, and migration status.
- Upgrade scripts create verified backups before continuing.

Older releases remain available through GitHub releases and tags. V2.1 is the recommended version for new installs and upgrades.

## Safe Upgrade First

Before replacing an existing install, use the safe upgrade wrapper. It creates a backup, verifies the archive, checks SQLite/JSON integrity, and stops if anything looks wrong.

Bare-metal:

```bash
python scripts/upgrade_to_v2_1.py baremetal
```

Docker:

```bash
python scripts/upgrade_to_v2_1.py docker
```

V1 JSON migration:

```bash
python scripts/upgrade_to_v2_1.py baremetal --v1-source /path/to/old/data/memories
```

See [docs/SAFE_UPGRADE.md](docs/SAFE_UPGRADE.md) for backup, restore, Docker volume, and rollback details.

## Install

### Fresh Bare-Metal Install

```bash
git clone https://github.com/mordang7/ContextKeep.git
cd ContextKeep
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

You can also run the installer:

```bash
python install.py
```

### Fresh Docker Install

```bash
git clone https://github.com/mordang7/ContextKeep.git
cd ContextKeep
docker compose up -d --build
```

Default ports:

| Service | URL |
|---------|-----|
| WebUI | `http://localhost:5000` |
| MCP HTTP | `http://localhost:5100/mcp` |

## Run

Local MCP over stdio:

```bash
python server.py
```

Remote MCP over HTTP:

```bash
python server.py --transport http --host 0.0.0.0 --port 5100
```

WebUI:

```bash
python webui.py --host 0.0.0.0 --port 5000
```

Then open:

```text
http://localhost:5000
```

## MCP Tools

ContextKeep V2.1 exposes 16 tools:

| Tool | Purpose |
|------|---------|
| `get_contextkeep_info` | Confirm version, storage path, database ID, schema, tools, and migration status |
| `list_categories` | List live user-editable categories |
| `create_category` | Create a category when no existing category fits |
| `update_category` | Rename or edit category metadata |
| `delete_category` | Delete an empty category or reassign memories |
| `merge_categories` | Merge one category into another |
| `list_memories` | List memory keys/titles, optionally filtered by category |
| `retrieve_memory` | Retrieve a memory by exact key |
| `search_memories` | Full-text search memory content |
| `list_recent_memories` | List recently updated memories |
| `store_memory` | Store or update a memory with categories |
| `update_categories` | Reassign one memory to one or more categories |
| `get_edit_history` | View edit history for a memory |
| `delete_memory` | Delete a memory permanently |
| `get_memory_stats` | Show memory/category counts and storage path |
| `export_memories` | Export all memories as JSON |

Recommended retrieval flow:

```text
list_categories -> list_memories -> retrieve_memory
```

Use `search_memories` for topic discovery, then retrieve the exact matching memory before relying on it.

## MCP Client Configuration

Most clients that support streamable HTTP:

```json
{
  "mcpServers": {
    "context-keep": {
      "url": "http://localhost:5100/mcp"
    }
  }
}
```

Antigravity IDE uses `serverURL`:

```json
{
  "mcpServers": {
    "context-keep": {
      "serverURL": "http://localhost:5100/mcp"
    }
  }
}
```

SSE fallback:

```json
{
  "mcpServers": {
    "context-keep": {
      "url": "http://localhost:5100/sse"
    }
  }
}
```

For a remote machine, replace `localhost` with the hostname or address of the machine running ContextKeep.

Do not keep an old SSH/stdin config active for the same `context-keep` server name. It may launch an older server that writes to a different database than the WebUI.

## Verify The Right Server

After connecting a client, call `get_contextkeep_info`.

Expected V2.1 values:

- `version`: `2.1.0`
- `schema_version`: `2`
- `storage_backend`: `sqlite`
- `storage_path`: `/app/data/contextkeep.db` in Docker, or your configured local path
- V2.1 tool list including `list_memories`, `list_categories`, `update_categories`, and `get_edit_history`

If an agent stores a memory but the WebUI cannot see it, compare WebUI `/api/info` with MCP `get_contextkeep_info`. The `database_id`, `storage_path`, and memory count should match.

## Backup And Restore

Create a verified bare-metal backup:

```bash
python scripts/backup_contextkeep.py baremetal --install-dir /path/to/contextkeep
```

Create a verified Docker backup:

```bash
python scripts/backup_contextkeep.py docker --volume <docker-volume-name>
```

Restore commands are written into every backup folder. The full guide is in [docs/SAFE_UPGRADE.md](docs/SAFE_UPGRADE.md).

If you use container auto-update software, keep an external backup routine. The safe upgrade scripts can verify backups before an upgrade, but unattended image replacement cannot ask you to confirm backup health.

## Docs

- [Safe Upgrade Guide](docs/SAFE_UPGRADE.md)
- [V2.1 Release Notes](RELEASE_NOTES_V2.1.md)
- [Docker V2.1 Guide](docs/DOCKER_V2_1.md)
- [Client Configuration](docs/CLIENT_CONFIGURATION.md)
- [Migration Guide](docs/MIGRATION_GUIDE.md)
- [Upgrading From V1](docs/UPGRADING_FROM_V1.md)
- [Directive Update Block](docs/DIRECTIVE_UPDATE.md)

## Changelog

### V2.1 Atlas

- SQLite database with FTS5 search.
- User-editable categories with multi-category memory assignment.
- WebUI category management.
- V1 JSON migration with legacy tag preservation.
- One-container Docker default for shared WebUI/MCP database access.
- `get_contextkeep_info` identity checks.
- Verified backup and restore tooling.
- Updated MCP client examples for HTTP, Antigravity, and SSE fallback.

### V1.3 Harbor

- Docker support.
- Modern Python packaging.
- New tools: `delete_memory`, `get_memory_stats`, `export_memories`.
- WebUI export.
- Packaging and code quality fixes.

### V1.2 Obsidian Lab

- Memory directory tool.
- Obsidian Lab UI redesign.
- Calendar and memory count improvements.

### V1.1

- Web dashboard.
- SSE transport support.
- Linux systemd service installer.
- Memory titles and timestamps.

### V1.0

- Core MCP server with persistent JSON-backed memory.
- Local stdio and remote access patterns.

## Contributing

Issues, feature ideas, and pull requests are welcome. If you build a client guide, migration recipe, or workflow pattern around ContextKeep, please share it.

### V1.3 Community Contributors

Thank you to everyone who contributed to the Harbor release:

- [@shuft](https://github.com/shuft) opened the Docker support request.
- [@Cyberdogs7](https://github.com/Cyberdogs7) contributed the initial Docker and Docker Compose implementation.
- [@frehov](https://github.com/frehov) contributed Dockerfile, `pyproject.toml`, `uv` support, and packaging fixes.
- [@thinkstylestudio](https://github.com/thinkstylestudio) supported the project through community advocacy.

## Support

If ContextKeep saves you time, tokens, or context-window pain, support is appreciated.

[![Ko-Fi](https://img.shields.io/badge/Ko--Fi-Support%20Me-F16061?style=flat&logo=ko-fi&logoColor=white)](https://ko-fi.com/geekj)

---

<div align="center">
  <sub>Built by GeekJohn</sub>
</div>
