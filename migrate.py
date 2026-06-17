#!/usr/bin/env python3
"""Migrate ContextKeep V1.x JSON memories into the V2 SQLite database."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from core.categories import categorize_memory
from core.database import Database, utcnow_iso


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = PROJECT_ROOT.parent / "ContextKeep" / "data" / "memories"
DEFAULT_TARGET = PROJECT_ROOT / "data" / "contextkeep.db"
HISTORY_RE = re.compile(r"\n\n---\n\*\*(?P<header>[^*\n]+)\*\*(?P<body>.*)$", re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate ContextKeep V1 JSON memories to V2 SQLite")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="V1 data/memories folder")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET, help="V2 SQLite database path")
    parser.add_argument("--check", action="store_true", help="Validate migration inputs without importing")
    parser.add_argument(
        "--reset-target",
        action="store_true",
        help="Delete and rebuild the target database if it already contains memories",
    )
    return parser.parse_args()


def validate_source(source: Path) -> list[Path]:
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"Source memory folder not found: {source}")
    files = sorted(source.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON memories found in: {source}")
    return files


def database_memory_count(target: Path) -> int:
    if not target.exists():
        return 0
    conn = sqlite3.connect(str(target))
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memories'"
        ).fetchone()
        if not row:
            return 0
        return int(conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0])
    finally:
        conn.close()


def remove_target_database(target: Path) -> None:
    for path in [target, Path(f"{target}-wal"), Path(f"{target}-shm")]:
        if path.exists():
            path.unlink()


def backup_source(source: Path, target: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = target.parent / f"v1_memories_backup_{stamp}.zip"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in source.glob("*.json"):
            archive.write(file_path, arcname=file_path.name)
    return backup_path


def strip_embedded_history(content: str) -> tuple[str, list[dict[str, Any]]]:
    match = HISTORY_RE.search(content or "")
    if not match:
        return content or "", []
    clean_content = (content or "")[: match.start()].rstrip()
    history = [
        {
            "header": match.group("header").strip(),
            "body": match.group("body").strip(),
        }
    ]
    return clean_content, history


def read_memory_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if "key" not in data or not data["key"]:
        data["key"] = path.stem
    if "title" not in data or not data["title"]:
        data["title"] = data["key"]
    if "content" not in data or data["content"] is None:
        data["content"] = ""
    if "tags" not in data or data["tags"] is None:
        data["tags"] = []
    return data


def generate_directive_update(project_root: Path) -> Path:
    docs_dir = project_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / "DIRECTIVE_UPDATE.md"
    path.write_text(
        """# ContextKeep V2 Directive Update

Use this block to replace V1 memory directives that mention `list_all_memories` or `tags`.

## Memory System

You are connected to an MCP server named `context-keep` for long-term memory.

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

## Removed V1 Concepts

- `list_all_memories` is removed in V2.
- `tags` are replaced by `categories`.
- Old tags are preserved as `legacy_tags` migration metadata only.

## Deletion Safety

If asked to delete a memory, ask for explicit confirmation before calling `delete_memory`.

If asked to delete a non-empty category, reassign or merge its memories first.
""",
        encoding="utf-8",
    )
    return path


def run_check(source: Path, target: Path) -> int:
    files = validate_source(source)
    Database.verify_fts5()
    target_count = database_memory_count(target)
    print("ContextKeep V2 migration check")
    print(f"  Source: {source}")
    print(f"  JSON memories: {len(files)}")
    print(f"  Target: {target}")
    print(f"  Existing target memories: {target_count}")
    print("  SQLite FTS5: OK")
    if target_count:
        print("  Target status: populated; use --reset-target to rebuild")
    else:
        print("  Target status: ready")
    return 0


def migrate(source: Path, target: Path, reset_target: bool = False) -> int:
    files = validate_source(source)
    Database.verify_fts5()
    existing_count = database_memory_count(target)
    if existing_count and not reset_target:
        raise RuntimeError(
            f"Target database already contains {existing_count} memories. "
            "Use --reset-target to rebuild it explicitly."
        )
    if reset_target:
        remove_target_database(target)

    target.parent.mkdir(parents=True, exist_ok=True)
    backup_path = backup_source(source, target)

    Database.set_path(target)
    from core.memory_manager import MemoryManager

    manager = MemoryManager()
    imported = 0
    skipped: list[str] = []

    for file_path in files:
        try:
            data = read_memory_file(file_path)
            clean_content, embedded_history = strip_embedded_history(data.get("content", ""))
            legacy_tags = data.get("tags") or []
            categories = categorize_memory(data["key"], data["title"], clean_content, legacy_tags)
            if not categories:
                categories = ["Uncategorized"]

            memory = manager.store_memory(
                key=data["key"],
                title=data["title"],
                content=clean_content,
                categories=categories,
                legacy_tags=legacy_tags,
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
                source="migration",
            )
            for item in embedded_history:
                manager._log_history(  # internal migration-only preservation
                    memory["id"],
                    "legacy_history_extracted",
                    item,
                    source="migration",
                )
            manager._log_history(
                memory["id"],
                "migrated",
                {
                    "source_file": str(file_path),
                    "legacy_tags": legacy_tags,
                    "categories": categories,
                },
                source="migration",
            )
            imported += 1
        except Exception as exc:
            skipped.append(f"{file_path.name}: {exc}")

    manager._recalculate_category_counts()
    Database.rebuild_fts()
    directive_path = generate_directive_update(PROJECT_ROOT)
    stats = manager.get_stats()

    print("ContextKeep V2 migration complete")
    print(f"  Backup: {backup_path}")
    print(f"  Target: {target}")
    print(f"  Imported: {imported}/{len(files)}")
    print(f"  Total memories in DB: {stats['total_memories']}")
    print("  Category distribution:")
    for category in stats["per_category_counts"]:
        if category["memory_count"]:
            print(f"    - {category['name']}: {category['memory_count']}")
    print(f"  Directive update: {directive_path}")
    if skipped:
        print("  Warnings:")
        for warning in skipped:
            print(f"    - {warning}")
    if imported != len(files):
        return 2
    return 0


def main() -> int:
    args = parse_args()
    try:
        source = args.source.resolve()
        target = args.target.resolve()
        if args.check:
            return run_check(source, target)
        return migrate(source, target, reset_target=args.reset_target)
    except Exception as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
