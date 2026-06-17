#!/usr/bin/env python3
"""Docker health check for the shared ContextKeep database."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.database import Database
from core.memory_manager import memory_manager


def main() -> int:
    Database.verify_writable()
    info = memory_manager.get_contextkeep_info()
    print(
        json.dumps(
            {
                "ok": True,
                "version": info["version"],
                "database_id": info.get("database_id", ""),
                "storage_path": info["storage_path"],
                "memory_count": info["migration_status"]["memory_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
