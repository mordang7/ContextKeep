"""SQLite database setup for ContextKeep V2.1 Atlas."""

from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .categories import STARTER_CATEGORIES


APP_VERSION = "2.1.0"
SCHEMA_VERSION = "2"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _default_db_path() -> Path:
    explicit_path = os.environ.get("CONTEXTKEEP_DB_PATH")
    if explicit_path:
        return Path(explicit_path).expanduser()
    data_dir = os.environ.get("CONTEXTKEEP_DATA_DIR")
    if data_dir:
        return Path(data_dir).expanduser() / "contextkeep.db"
    return PROJECT_ROOT / "data" / "contextkeep.db"


DEFAULT_DB_PATH = _default_db_path()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT COLLATE NOCASE UNIQUE NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    icon TEXT NOT NULL DEFAULT 'folder',
    is_starter INTEGER NOT NULL DEFAULT 0,
    memory_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT COLLATE NOCASE UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    legacy_tags TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    lines INTEGER NOT NULL DEFAULT 0,
    chars INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS memory_categories (
    memory_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    assigned_at TEXT NOT NULL,
    PRIMARY KEY (memory_id, category_id),
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS edit_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    source TEXT NOT NULL DEFAULT 'mcp',
    timestamp TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    key,
    title,
    content,
    content=memories,
    content_rowid=id
);

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, key, title, content)
    VALUES (new.id, new.key, new.title, new.content);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, key, title, content)
    VALUES ('delete', old.id, old.key, old.title, old.content);
END;

CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, key, title, content)
    VALUES ('delete', old.id, old.key, old.title, old.content);
    INSERT INTO memories_fts(rowid, key, title, content)
    VALUES (new.id, new.key, new.title, new.content);
END;

CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);
CREATE INDEX IF NOT EXISTS idx_memories_updated ON memories(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_categories_memory ON memory_categories(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_categories_category ON memory_categories(category_id);
CREATE INDEX IF NOT EXISTS idx_edit_history_memory ON edit_history(memory_id);
"""


def utcnow_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Database:
    """Thread-local SQLite connection manager for a shared SQLite database."""

    _local = threading.local()
    _db_path: Path = DEFAULT_DB_PATH

    @classmethod
    def set_path(cls, path: str | Path) -> None:
        cls.close()
        cls._db_path = Path(path)

    @classmethod
    def path(cls) -> Path:
        return cls._db_path

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        conn: Optional[sqlite3.Connection] = getattr(cls._local, "conn", None)
        if conn is None:
            cls._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(cls._db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=5000")
            cls._local.conn = conn
        return conn

    @classmethod
    def close(cls) -> None:
        conn: Optional[sqlite3.Connection] = getattr(cls._local, "conn", None)
        if conn is not None:
            conn.close()
            cls._local.conn = None

    @classmethod
    def initialize(cls) -> None:
        conn = cls.get_connection()
        conn.executescript(SCHEMA_SQL)
        cls._seed_schema_meta(conn)
        cls._seed_starter_categories(conn)
        conn.commit()

    @classmethod
    def _seed_schema_meta(cls, conn: sqlite3.Connection) -> None:
        now = utcnow_iso()
        for key, value in {
            "schema_version": SCHEMA_VERSION,
            "app_version": APP_VERSION,
            "storage_backend": "sqlite",
        }.items():
            conn.execute(
                """
                INSERT INTO schema_meta(key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value, now),
            )
        existing_id = conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'database_id'"
        ).fetchone()
        if not existing_id:
            conn.execute(
                """
                INSERT INTO schema_meta(key, value, updated_at)
                VALUES ('database_id', ?, ?)
                """,
                (str(uuid.uuid4()), now),
            )

    @classmethod
    def _seed_starter_categories(cls, conn: sqlite3.Connection) -> None:
        now = utcnow_iso()
        for category in STARTER_CATEGORIES:
            conn.execute(
                """
                INSERT INTO categories(name, description, icon, is_starter, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(name) DO NOTHING
                """,
                (
                    category["name"],
                    category["description"],
                    category["icon"],
                    now,
                    now,
                ),
            )

    @classmethod
    def rebuild_fts(cls) -> None:
        conn = cls.get_connection()
        conn.execute("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')")
        conn.commit()

    @classmethod
    def verify_fts5(cls) -> None:
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute("CREATE VIRTUAL TABLE fts_check USING fts5(content)")
        finally:
            conn.close()

    @classmethod
    def verify_writable(cls) -> None:
        """Write a tiny heartbeat so container health checks catch read-only DBs."""
        cls.initialize()
        now = utcnow_iso()
        conn = cls.get_connection()
        conn.execute(
            """
            INSERT INTO schema_meta(key, value, updated_at)
            VALUES ('last_writable_check', ?, ?)
            ON CONFLICT(key) DO UPDATE
            SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (now, now),
        )
        conn.commit()

    @classmethod
    def database_id(cls) -> str:
        cls.initialize()
        row = cls.get_connection().execute(
            "SELECT value FROM schema_meta WHERE key = 'database_id'"
        ).fetchone()
        return str(row["value"]) if row else ""
