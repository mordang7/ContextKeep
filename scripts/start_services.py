#!/usr/bin/env python3
"""Run the MCP server and WebUI in one container against one shared database."""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.database import Database
from core.memory_manager import memory_manager


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start ContextKeep V2.1 Docker services")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--mcp-port", type=int, default=5100)
    parser.add_argument("--webui-port", type=int, default=5000)
    parser.add_argument("--mcp-transport", choices=["http", "sse"], default="http")
    return parser.parse_args()


def terminate(processes: list[subprocess.Popen[object]]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    deadline = time.time() + 10
    for process in processes:
        while process.poll() is None and time.time() < deadline:
            time.sleep(0.1)
        if process.poll() is None:
            process.kill()


def main() -> int:
    args = parse_args()
    Database.verify_writable()
    info = memory_manager.get_contextkeep_info()
    migration = info["migration_status"]
    print(
        "ContextKeep V2.1 starting with "
        f"db={info['storage_path']} "
        f"database_id={info.get('database_id', '')} "
        f"memories={migration['memory_count']}",
        flush=True,
    )

    commands = [
        [
            sys.executable,
            str(ROOT / "server.py"),
            "--transport",
            args.mcp_transport,
            "--host",
            args.host,
            "--port",
            str(args.mcp_port),
        ],
        [
            sys.executable,
            str(ROOT / "webui.py"),
            "--host",
            args.host,
            "--port",
            str(args.webui_port),
        ],
    ]
    processes = [subprocess.Popen(command) for command in commands]

    def handle_stop(_signum: int, _frame: object) -> None:
        terminate(processes)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    while True:
        for process in processes:
            code = process.poll()
            if code is not None:
                terminate(processes)
                return int(code)
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
