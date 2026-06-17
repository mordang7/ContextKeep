"""SQLite-backed memory manager for ContextKeep V2.1 Atlas."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, List, Optional

from .database import APP_VERSION, Database, SCHEMA_VERSION, utcnow_iso


CREDENTIAL_CATEGORY = "Credentials & Access"
SENSITIVE_MARKER = "[masked credential memory]"


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


class MemoryManager:
    def __init__(self) -> None:
        Database.initialize()

    @property
    def db_path(self) -> Path:
        return Database.path()

    def _conn(self) -> sqlite3.Connection:
        return Database.get_connection()

    def _parse_categories(self, categories: str | Iterable[str] | None) -> list[str]:
        if categories is None:
            return []
        if isinstance(categories, str):
            values = [part.strip() for part in categories.split(",")]
        else:
            values = [str(part).strip() for part in categories]
        seen: set[str] = set()
        parsed: list[str] = []
        for value in values:
            if not value:
                continue
            key = value.casefold()
            if key not in seen:
                seen.add(key)
                parsed.append(value)
        return parsed

    def _get_category_by_name(self, name: str) -> dict[str, Any] | None:
        row = self._conn().execute(
            "SELECT * FROM categories WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        return _row_to_dict(row)

    def _get_category_by_id(self, category_id: int) -> dict[str, Any] | None:
        row = self._conn().execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
        return _row_to_dict(row)

    def _ensure_category(
        self,
        name: str,
        description: str = "",
        icon: str = "folder",
        is_starter: bool = False,
    ) -> dict[str, Any]:
        existing = self._get_category_by_name(name)
        if existing:
            return existing
        now = utcnow_iso()
        cur = self._conn().execute(
            """
            INSERT INTO categories(name, description, icon, is_starter, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, description or "", icon or "folder", int(is_starter), now, now),
        )
        return self._get_category_by_id(cur.lastrowid) or {}

    def _categories_for_memory(self, memory_id: int) -> list[dict[str, Any]]:
        rows = self._conn().execute(
            """
            SELECT c.id, c.name, c.description, c.icon, c.is_starter, c.memory_count
            FROM categories c
            JOIN memory_categories mc ON mc.category_id = c.id
            WHERE mc.memory_id = ?
            ORDER BY c.name COLLATE NOCASE
            """,
            (memory_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def _recalculate_category_counts(self) -> None:
        self._conn().execute(
            """
            UPDATE categories
            SET memory_count = (
                SELECT COUNT(*) FROM memory_categories mc WHERE mc.category_id = categories.id
            )
            """
        )

    def _log_history(
        self,
        memory_id: int,
        action: str,
        details: dict[str, Any] | str | None = None,
        source: str = "mcp",
    ) -> None:
        if isinstance(details, str):
            details_json = json.dumps({"message": details}, ensure_ascii=False)
        else:
            details_json = json.dumps(details or {}, ensure_ascii=False)
        self._conn().execute(
            """
            INSERT INTO edit_history(memory_id, action, details, source, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (memory_id, action, details_json, source, utcnow_iso()),
        )

    def _format_memory(self, row: sqlite3.Row, include_history: bool = False) -> dict[str, Any]:
        memory = dict(row)
        memory["categories"] = self._categories_for_memory(memory["id"])
        try:
            memory["legacy_tags"] = json.loads(memory.get("legacy_tags") or "[]")
        except json.JSONDecodeError:
            memory["legacy_tags"] = []
        if include_history:
            memory["edit_history"] = self.get_edit_history(memory["key"], limit=10)
        return memory

    def _memory_by_key(self, key: str) -> sqlite3.Row | None:
        return self._conn().execute(
            "SELECT * FROM memories WHERE key = ? COLLATE NOCASE", (key,)
        ).fetchone()

    def is_credential_memory(self, memory: dict[str, Any]) -> bool:
        return any(
            category.get("name", "").casefold() == CREDENTIAL_CATEGORY.casefold()
            for category in memory.get("categories", [])
        )

    def mask_memory_for_listing(self, memory: dict[str, Any]) -> dict[str, Any]:
        if self.is_credential_memory(memory):
            masked = dict(memory)
            masked["snippet"] = SENSITIVE_MARKER
            masked["content"] = SENSITIVE_MARKER
            masked["is_masked"] = True
            return masked
        memory["is_masked"] = False
        return memory

    def store_memory(
        self,
        key: str,
        content: str,
        categories: str | Iterable[str] | None = None,
        title: str | None = None,
        legacy_tags: Iterable[str] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        source: str = "mcp",
    ) -> dict[str, Any]:
        if not key or not key.strip():
            raise ValueError("Memory key is required")
        key = key.strip()
        content = content or ""
        category_names = self._parse_categories(categories) or ["Uncategorized"]
        now = updated_at or utcnow_iso()
        existing = self._memory_by_key(key)
        is_update = existing is not None
        created_at_final = existing["created_at"] if existing else (created_at or now)
        resolved_title = (title or "").strip() or (existing["title"] if existing else key)
        legacy_json = (
            existing["legacy_tags"]
            if existing and legacy_tags is None
            else json.dumps(list(legacy_tags or []), ensure_ascii=False)
        )

        conn = self._conn()
        with conn:
            if existing:
                conn.execute(
                    """
                    UPDATE memories
                    SET title = ?, content = ?, legacy_tags = ?, updated_at = ?, lines = ?, chars = ?
                    WHERE id = ?
                    """,
                    (
                        resolved_title,
                        content,
                        legacy_json,
                        now,
                        len(content.splitlines()),
                        len(content),
                        existing["id"],
                    ),
                )
                memory_id = int(existing["id"])
            else:
                cur = conn.execute(
                    """
                    INSERT INTO memories(key, title, content, legacy_tags, created_at, updated_at, lines, chars)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        key,
                        resolved_title,
                        content,
                        legacy_json,
                        created_at_final,
                        now,
                        len(content.splitlines()),
                        len(content),
                    ),
                )
                memory_id = int(cur.lastrowid)

            old_categories = {
                row["name"]
                for row in conn.execute(
                    """
                    SELECT c.name
                    FROM categories c
                    JOIN memory_categories mc ON mc.category_id = c.id
                    WHERE mc.memory_id = ?
                    """,
                    (memory_id,),
                )
            }
            conn.execute("DELETE FROM memory_categories WHERE memory_id = ?", (memory_id,))
            for category_name in category_names:
                category = self._ensure_category(category_name)
                conn.execute(
                    """
                    INSERT OR IGNORE INTO memory_categories(memory_id, category_id, assigned_at)
                    VALUES (?, ?, ?)
                    """,
                    (memory_id, category["id"], now),
                )

            self._recalculate_category_counts()
            new_categories = set(category_names)
            action = "updated" if is_update else "created"
            self._log_history(
                memory_id,
                action,
                {
                    "title": resolved_title,
                    "categories": sorted(new_categories),
                    "chars": len(content),
                },
                source=source,
            )
            if is_update and old_categories != new_categories:
                self._log_history(
                    memory_id,
                    "categories_changed",
                    {
                        "from": sorted(old_categories),
                        "to": sorted(new_categories),
                    },
                    source=source,
                )

        result = self.retrieve_memory(key)
        if result is None:
            raise RuntimeError(f"Stored memory could not be retrieved: {key}")
        return result

    def retrieve_memory(self, key: str) -> Optional[dict[str, Any]]:
        row = self._memory_by_key(key)
        if not row:
            return None
        return self._format_memory(row, include_history=True)

    def list_categories(self) -> list[dict[str, Any]]:
        rows = self._conn().execute(
            """
            SELECT id, name, description, icon, is_starter, memory_count, created_at, updated_at
            FROM categories
            ORDER BY CASE WHEN name = 'Uncategorized' THEN 1 ELSE 0 END,
                     memory_count DESC,
                     name COLLATE NOCASE
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def list_memories(
        self,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
        mask_credentials: bool = False,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit or 50), 500))
        offset = max(0, int(offset or 0))
        params: list[Any] = []
        if category:
            sql = """
                SELECT DISTINCT m.*, SUBSTR(m.content, 1, 160) AS snippet
                FROM memories m
                JOIN memory_categories mc ON mc.memory_id = m.id
                JOIN categories c ON c.id = mc.category_id
                WHERE c.name = ? COLLATE NOCASE
                ORDER BY m.updated_at DESC
                LIMIT ? OFFSET ?
            """
            params = [category, limit, offset]
        else:
            sql = """
                SELECT m.*, SUBSTR(m.content, 1, 160) AS snippet
                FROM memories m
                ORDER BY m.updated_at DESC
                LIMIT ? OFFSET ?
            """
            params = [limit, offset]

        rows = self._conn().execute(sql, params).fetchall()
        memories = [self._format_memory(row) for row in rows]
        if mask_credentials:
            memories = [self.mask_memory_for_listing(memory) for memory in memories]
        return memories

    def list_recent_memories(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.list_memories(limit=limit)

    def search_memories(
        self,
        query: str,
        category: str | None = None,
        limit: int = 20,
        mask_credentials: bool = False,
    ) -> list[dict[str, Any]]:
        query = (query or "").strip()
        if not query:
            return []
        limit = max(1, min(int(limit or 20), 100))
        match_query = self._fts_query(query)

        if category:
            rows = self._conn().execute(
                """
                SELECT DISTINCT m.*,
                       snippet(memories_fts, 2, '<mark>', '</mark>', '...', 32) AS snippet
                FROM memories_fts
                JOIN memories m ON m.id = memories_fts.rowid
                JOIN memory_categories mc ON mc.memory_id = m.id
                JOIN categories c ON c.id = mc.category_id
                WHERE memories_fts MATCH ? AND c.name = ? COLLATE NOCASE
                ORDER BY rank
                LIMIT ?
                """,
                (match_query, category, limit),
            ).fetchall()
        else:
            rows = self._conn().execute(
                """
                SELECT m.*, snippet(memories_fts, 2, '<mark>', '</mark>', '...', 32) AS snippet
                FROM memories_fts
                JOIN memories m ON m.id = memories_fts.rowid
                WHERE memories_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (match_query, limit),
            ).fetchall()

        memories = [self._format_memory(row) for row in rows]
        if mask_credentials:
            memories = [self.mask_memory_for_listing(memory) for memory in memories]
        return memories

    def _fts_query(self, query: str) -> str:
        terms = [term.replace('"', '""') for term in query.split() if term.strip()]
        if not terms:
            return '""'
        return " OR ".join(f'"{term}"' for term in terms)

    def delete_memory(self, key: str) -> bool:
        row = self._memory_by_key(key)
        if not row:
            return False
        with self._conn():
            self._conn().execute("DELETE FROM memories WHERE id = ?", (row["id"],))
            self._recalculate_category_counts()
        return True

    def create_category(
        self,
        name: str,
        description: str = "",
        icon: str = "folder",
        source: str = "mcp",
    ) -> dict[str, Any]:
        if not name or not name.strip():
            raise ValueError("Category name is required")
        with self._conn():
            category = self._ensure_category(name.strip(), description, icon, is_starter=False)
        return category

    def update_category(
        self,
        category_id: int,
        name: str | None = None,
        description: str | None = None,
        icon: str | None = None,
        source: str = "mcp",
    ) -> dict[str, Any]:
        category = self._get_category_by_id(int(category_id))
        if not category:
            raise KeyError(f"Category not found: {category_id}")
        new_name = (name or category["name"]).strip()
        if not new_name:
            raise ValueError("Category name is required")
        with self._conn():
            self._conn().execute(
                """
                UPDATE categories
                SET name = ?, description = ?, icon = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    new_name,
                    description if description is not None else category["description"],
                    icon if icon is not None else category["icon"],
                    utcnow_iso(),
                    category_id,
                ),
            )
        updated = self._get_category_by_id(int(category_id))
        if not updated:
            raise RuntimeError("Updated category could not be retrieved")
        return updated

    def delete_category(self, category_id: int, reassign_to: int | None = None) -> dict[str, Any]:
        category_id = int(category_id)
        category = self._get_category_by_id(category_id)
        if not category:
            raise KeyError(f"Category not found: {category_id}")
        count = int(category["memory_count"])
        if count > 0 and not reassign_to:
            raise ValueError("Non-empty category requires reassign_to or merge")
        if reassign_to and int(reassign_to) == category_id:
            raise ValueError("Cannot reassign a category to itself")

        with self._conn():
            moved = 0
            if count > 0:
                target = self._get_category_by_id(int(reassign_to))
                if not target:
                    raise KeyError(f"Target category not found: {reassign_to}")
                rows = self._conn().execute(
                    "SELECT memory_id FROM memory_categories WHERE category_id = ?",
                    (category_id,),
                ).fetchall()
                for row in rows:
                    self._conn().execute(
                        """
                        INSERT OR IGNORE INTO memory_categories(memory_id, category_id, assigned_at)
                        VALUES (?, ?, ?)
                        """,
                        (row["memory_id"], reassign_to, utcnow_iso()),
                    )
                    moved += 1
            self._conn().execute("DELETE FROM memory_categories WHERE category_id = ?", (category_id,))
            self._conn().execute("DELETE FROM categories WHERE id = ?", (category_id,))
            self._recalculate_category_counts()
        return {"deleted": category, "reassigned_count": moved}

    def merge_categories(self, source_id: int, target_id: int) -> dict[str, Any]:
        source_id = int(source_id)
        target_id = int(target_id)
        if source_id == target_id:
            raise ValueError("Source and target categories must be different")
        source = self._get_category_by_id(source_id)
        target = self._get_category_by_id(target_id)
        if not source:
            raise KeyError(f"Source category not found: {source_id}")
        if not target:
            raise KeyError(f"Target category not found: {target_id}")

        with self._conn():
            rows = self._conn().execute(
                "SELECT memory_id FROM memory_categories WHERE category_id = ?",
                (source_id,),
            ).fetchall()
            moved = 0
            for row in rows:
                self._conn().execute(
                    """
                    INSERT OR IGNORE INTO memory_categories(memory_id, category_id, assigned_at)
                    VALUES (?, ?, ?)
                    """,
                    (row["memory_id"], target_id, utcnow_iso()),
                )
                moved += 1
            self._conn().execute("DELETE FROM memory_categories WHERE category_id = ?", (source_id,))
            self._conn().execute("DELETE FROM categories WHERE id = ?", (source_id,))
            self._recalculate_category_counts()
        return {"source": source, "target": self._get_category_by_id(target_id), "moved_count": moved}

    def update_categories(
        self,
        key: str,
        categories: str | Iterable[str],
        source: str = "mcp",
    ) -> dict[str, Any]:
        memory = self.retrieve_memory(key)
        if not memory:
            raise KeyError(f"Memory not found: {key}")
        return self.store_memory(
            key=memory["key"],
            title=memory["title"],
            content=memory["content"],
            categories=categories,
            legacy_tags=memory.get("legacy_tags", []),
            source=source,
        )

    def get_stats(self) -> dict[str, Any]:
        conn = self._conn()
        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        chars = conn.execute("SELECT COALESCE(SUM(chars), 0) FROM memories").fetchone()[0]
        categories = self.list_categories()
        return {
            "total_memories": total,
            "total_count": total,
            "total_chars": chars,
            "total_categories": len(categories),
            "per_category_counts": categories,
            "storage_path": str(self.db_path),
        }

    def export_all(self) -> list[dict[str, Any]]:
        rows = self._conn().execute(
            "SELECT * FROM memories ORDER BY updated_at DESC"
        ).fetchall()
        return [self._format_memory(row, include_history=True) for row in rows]

    def get_edit_history(self, key: str, limit: int = 10) -> list[dict[str, Any]]:
        row = self._memory_by_key(key)
        if not row:
            return []
        limit = max(1, min(int(limit or 10), 200))
        rows = self._conn().execute(
            """
            SELECT action, details, source, timestamp
            FROM edit_history
            WHERE memory_id = ?
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
            """,
            (row["id"], limit),
        ).fetchall()
        history: list[dict[str, Any]] = []
        for item in rows:
            details_raw = item["details"] or "{}"
            try:
                details = json.loads(details_raw)
            except json.JSONDecodeError:
                details = {"raw": details_raw}
            history.append(
                {
                    "action": item["action"],
                    "details": details,
                    "source": item["source"],
                    "timestamp": item["timestamp"],
                }
            )
        return history

    def get_contextkeep_info(self) -> dict[str, Any]:
        meta_rows = self._conn().execute("SELECT key, value FROM schema_meta").fetchall()
        meta = {row["key"]: row["value"] for row in meta_rows}
        return {
            "name": "ContextKeep",
            "version": APP_VERSION,
            "schema_version": meta.get("schema_version", SCHEMA_VERSION),
            "storage_backend": meta.get("storage_backend", "sqlite"),
            "storage_path": str(self.db_path),
            "database_id": meta.get("database_id", Database.database_id()),
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
                "get_contextkeep_info",
            ],
            "migration_status": self._migration_status(),
        }

    def _migration_status(self) -> dict[str, Any]:
        count = self._conn().execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        return {
            "has_memories": bool(count),
            "memory_count": count,
            "database_exists": self.db_path.exists(),
        }


memory_manager = MemoryManager()
