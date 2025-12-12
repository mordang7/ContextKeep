import json
import os
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configuration
# Store data relative to the project root to ensure portability between Windows/Linux in shared folders
PROJECT_ROOT = Path(__file__).parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "memories"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class MemoryManager:
    def __init__(self):
        self.cache_dir = CACHE_DIR

    def _get_file_path(self, key: str) -> Path:
        """Get the file path for a given memory key."""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.json"

    def store_memory(
        self, key: str, content: str, tags: List[str] = None, title: str = None
    ) -> Dict[str, Any]:
        """Store a new memory or overwrite an existing one."""
        file_path = self._get_file_path(key)
        # Use local system timezone
        now = datetime.now().astimezone().isoformat()

        # Note: Edit history logging is now handled by the caller (server.py or webui.py)
        # to prevent duplicate logs and allow for more context-aware messages.

        memory_data = {
            "key": key,
            "title": title or key,  # Default title to key if not provided
            "content": content,
            "tags": tags or [],
            "created_at": now,
            "updated_at": now,
            "lines": len(content.splitlines()),
            "chars": len(content),
        }

        # If updating, preserve created_at and existing title if new one not provided
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    memory_data["created_at"] = existing.get("created_at", now)
                    if not title:
                        memory_data["title"] = existing.get("title", key)
            except:
                pass  # Overwrite if corrupt

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, indent=2, ensure_ascii=False)

        return memory_data

    def retrieve_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a memory by key."""
        file_path = self._get_file_path(key)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception as e:
            # Silently fail - don't print to stdout as it corrupts MCP stdio transport
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"DEBUG: loaded data for key={key}")
                return data
        except Exception as e:
            print(f"DEBUG: exception loading {key}: {e}")
            # Silently fail - don't print to stdout as it corrupts MCP stdio transport
            return None

    def list_memories(self) -> List[Dict[str, Any]]:
        """List all memories with metadata."""
        memories = []
        for file_path in self.cache_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Add a snippet for display
                    data["snippet"] = (
                        data["content"][:100] + "..."
                        if len(data["content"]) > 100
                        else data["content"]
                    )
                    # Ensure title exists for legacy memories
                    if "title" not in data:
                        data["title"] = data["key"]
                    memories.append(data)
            except:
                continue

        # Sort by updated_at descending
        return sorted(memories, key=lambda x: x.get("updated_at", ""), reverse=True)

    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """Search memories by key, title, or content."""
        query = query.lower()
        results = []
        all_memories = self.list_memories()

        for mem in all_memories:
            if (
                query in mem["key"].lower()
                or query in mem.get("title", "").lower()
                or query in mem["content"].lower()
            ):
                results.append(mem)

        return results

    def delete_memory(self, key: str) -> bool:
        """Delete a memory by key."""
        file_path = self._get_file_path(key)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        memories = self.list_memories()
        return {
            "total_count": len(memories),
            "total_chars": sum(m["chars"] for m in memories),
            "storage_path": str(self.cache_dir),
        }


# Global instance
memory_manager = MemoryManager()
