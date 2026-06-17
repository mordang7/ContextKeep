#!/usr/bin/env python3
"""ContextKeep V2.1 bare-metal installer."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


APP_VERSION = "2.1.0"
PROJECT_ROOT = Path(__file__).resolve().parent


def print_header() -> None:
    print("=" * 64)
    print("        ContextKeep V2.1 Atlas - Installation Wizard")
    print("=" * 64)
    print()


def check_python() -> None:
    print("[*] Checking Python version...")
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or higher is required.")
    print(f"[+] Python {sys.version_info.major}.{sys.version_info.minor} detected.")


def has_uv() -> bool:
    return shutil.which("uv") is not None


def venv_python() -> Path:
    if os.name == "nt":
        return PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    return PROJECT_ROOT / ".venv" / "bin" / "python"


def create_venv() -> Path:
    python_path = venv_python()
    if python_path.exists():
        print("[+] Existing virtual environment found.")
        return python_path
    print("[*] Creating virtual environment...")
    subprocess.check_call([sys.executable, "-m", "venv", str(PROJECT_ROOT / ".venv")])
    return python_path


def install_dependencies(python_path: Path) -> None:
    if has_uv():
        print("[*] Installing dependencies with uv...")
        try:
            subprocess.check_call(["uv", "sync"], cwd=PROJECT_ROOT)
            return
        except subprocess.CalledProcessError:
            print("[!] uv sync failed; falling back to pip.")
    print("[*] Installing dependencies with pip...")
    subprocess.check_call([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], cwd=PROJECT_ROOT)
    subprocess.check_call([str(python_path), "-m", "pip", "install", "-r", "requirements.txt"], cwd=PROJECT_ROOT)


def write_config(python_path: Path) -> Path:
    config = {
        "mcpServers": {
            "context-keep": {
                "command": str(python_path.resolve()),
                "args": [str((PROJECT_ROOT / "server.py").resolve())],
            }
        }
    }
    config_path = PROJECT_ROOT / "mcp_config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"[+] Wrote local stdio MCP config: {config_path.name}")
    return config_path


def main() -> int:
    print_header()
    check_python()
    print("For upgrades, run the safe upgrade wrapper first:")
    print("  python scripts/upgrade_to_v2_1.py baremetal")
    print()
    print("For a fresh local install, this wizard creates .venv, installs dependencies, and writes mcp_config.json.")
    answer = input("Proceed with fresh/update-in-place local install? [Y/n]: ").strip().lower()
    if answer == "n":
        print("Installation cancelled.")
        return 0

    python_path = create_venv()
    install_dependencies(python_path)
    config_path = write_config(python_path)

    print()
    print("=" * 64)
    print("        Installation Complete")
    print("=" * 64)
    print(f"ContextKeep {APP_VERSION} is ready.")
    print(f"Copy {config_path.name} into your MCP client config, then restart the client.")
    print()
    print("Run locally:")
    print(f"  {python_path} server.py")
    print(f"  {python_path} webui.py --host 127.0.0.1 --port 5000")
    print()
    print("Remote HTTP MCP:")
    print(f"  {python_path} server.py --transport http --host 0.0.0.0 --port 5100")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
