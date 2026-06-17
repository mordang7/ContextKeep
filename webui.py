#!/usr/bin/env python3
"""ContextKeep V2.1 Atlas WebUI server."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, Response, jsonify, render_template, request

from core.database import Database
from core.memory_manager import SENSITIVE_MARKER, memory_manager


app = Flask(__name__)


def ok(**payload: Any):
    return jsonify({"success": True, **payload})


def fail(message: str, status: int = 400):
    return jsonify({"success": False, "error": message}), status


def public_memory(memory: dict[str, Any], reveal: bool = False) -> dict[str, Any]:
    if not reveal and memory_manager.is_credential_memory(memory):
        masked = dict(memory)
        masked["content"] = SENSITIVE_MARKER
        masked["snippet"] = SENSITIVE_MARKER
        masked["is_masked"] = True
        return masked
    memory["is_masked"] = False
    return memory


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["GET"])
def info():
    return ok(info=memory_manager.get_contextkeep_info())


@app.route("/api/categories", methods=["GET"])
def list_categories():
    return ok(categories=memory_manager.list_categories())


@app.route("/api/categories", methods=["POST"])
def create_category():
    data = request.get_json(force=True) or {}
    try:
        category = memory_manager.create_category(
            data.get("name", ""),
            data.get("description", ""),
            data.get("icon", "folder"),
            source="webui",
        )
        return ok(category=category)
    except Exception as exc:
        return fail(str(exc))


@app.route("/api/categories/<int:category_id>", methods=["PUT"])
def update_category(category_id: int):
    data = request.get_json(force=True) or {}
    try:
        category = memory_manager.update_category(
            category_id,
            name=data.get("name"),
            description=data.get("description"),
            icon=data.get("icon"),
            source="webui",
        )
        return ok(category=category)
    except KeyError as exc:
        return fail(str(exc), 404)
    except Exception as exc:
        return fail(str(exc))


@app.route("/api/categories/<int:category_id>", methods=["DELETE"])
def delete_category(category_id: int):
    reassign_to_raw = request.args.get("reassign_to", "")
    reassign_to = int(reassign_to_raw) if reassign_to_raw else None
    try:
        result = memory_manager.delete_category(category_id, reassign_to)
        return ok(result=result)
    except KeyError as exc:
        return fail(str(exc), 404)
    except Exception as exc:
        return fail(str(exc))


@app.route("/api/categories/<int:category_id>/merge", methods=["POST"])
def merge_category(category_id: int):
    data = request.get_json(force=True) or {}
    try:
        result = memory_manager.merge_categories(category_id, int(data.get("target_id")))
        return ok(result=result)
    except KeyError as exc:
        return fail(str(exc), 404)
    except Exception as exc:
        return fail(str(exc))


@app.route("/api/memories", methods=["GET"])
def list_memories():
    category = request.args.get("category") or None
    limit = int(request.args.get("limit", "50"))
    offset = int(request.args.get("offset", "0"))
    memories = memory_manager.list_memories(
        category=category,
        limit=limit,
        offset=offset,
        mask_credentials=True,
    )
    return ok(memories=memories)


@app.route("/api/memories/<path:key>", methods=["GET"])
def get_memory(key: str):
    memory = memory_manager.retrieve_memory(key)
    if not memory:
        return fail("Memory not found", 404)
    reveal = request.args.get("reveal") == "1"
    return ok(memory=public_memory(memory, reveal=reveal))


@app.route("/api/memories", methods=["POST"])
def create_memory():
    data = request.get_json(force=True) or {}
    try:
        memory = memory_manager.store_memory(
            key=data.get("key", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            categories=data.get("categories", []),
            source="webui",
        )
        return ok(memory=memory)
    except Exception as exc:
        return fail(str(exc))


@app.route("/api/memories/<path:key>", methods=["PUT"])
def update_memory(key: str):
    data = request.get_json(force=True) or {}
    existing = memory_manager.retrieve_memory(key)
    if not existing:
        return fail("Memory not found", 404)
    try:
        memory = memory_manager.store_memory(
            key=key,
            title=data.get("title", existing.get("title", key)),
            content=data.get("content", existing.get("content", "")),
            categories=data.get(
                "categories",
                [category["name"] for category in existing.get("categories", [])],
            ),
            legacy_tags=existing.get("legacy_tags", []),
            source="webui",
        )
        return ok(memory=memory)
    except Exception as exc:
        return fail(str(exc))


@app.route("/api/memories/<path:key>", methods=["DELETE"])
def delete_memory(key: str):
    if memory_manager.delete_memory(key):
        return ok()
    return fail("Memory not found", 404)


@app.route("/api/memories/<path:key>/history", methods=["GET"])
def get_history(key: str):
    limit = int(request.args.get("limit", "10"))
    return ok(history=memory_manager.get_edit_history(key, limit))


@app.route("/api/search", methods=["GET"])
def search_memories():
    query = request.args.get("q", "")
    category = request.args.get("category") or None
    memories = memory_manager.search_memories(
        query=query,
        category=category,
        mask_credentials=True,
    )
    return ok(memories=memories)


@app.route("/api/stats", methods=["GET"])
def stats():
    return ok(stats=memory_manager.get_stats())


@app.route("/api/export", methods=["GET"])
def export_all():
    memories = memory_manager.export_all()
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"contextkeep_v2_backup_{timestamp}.json"
    return Response(
        json.dumps(memories, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-ContextKeep-Warning": "Export includes full memory content, including credentials.",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="ContextKeep V2.1 Atlas WebUI")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    Database.verify_writable()
    info = memory_manager.get_contextkeep_info()
    print(
        "Starting ContextKeep V2.1 Atlas WebUI "
        f"at http://{args.host}:{args.port}; "
        f"db={info['storage_path']}; database_id={info.get('database_id', '')}; "
        f"memories={info['migration_status']['memory_count']}"
    )
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
