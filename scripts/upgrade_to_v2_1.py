#!/usr/bin/env python3
"""Safe ContextKeep V2.1 upgrade wrapper.

This script always creates and verifies a backup before making upgrade changes.
It is intentionally conservative: when a backup, migration, build, or health
check fails, the script stops and prints the restore command.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from backup_contextkeep import BackupResult, create_baremetal_backup, create_docker_backup  # noqa: E402


def run_command(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print(f"+ {' '.join(command)}")
    subprocess.run(command, cwd=str(cwd) if cwd else None, env=env, check=True)


def docker_compose_command(compose_file: Path) -> list[str]:
    return ["docker", "compose", "-f", str(compose_file)]


def print_restore_hint(result: BackupResult, mode: str, target: str) -> None:
    print("Verified backup created before upgrade.")
    print(f"  Backup folder: {result.backup_dir}")
    print(f"  Archive: {result.archive_path}")
    print("")
    print("Restore command if you need to roll back:")
    if mode == "docker":
        print(
            "  python scripts/restore_contextkeep.py docker "
            f"--backup \"{result.archive_path}\" --volume <docker-volume-name> --confirm"
        )
    else:
        print(
            "  python scripts/restore_contextkeep.py baremetal "
            f"--backup \"{result.archive_path}\" --target-dir \"{target}\" --confirm"
        )


def run_baremetal_upgrade(args: argparse.Namespace) -> int:
    backup = create_baremetal_backup(args.install_dir, args.backup_output_dir)
    print_restore_hint(backup, "baremetal", str(args.install_dir))

    env = os.environ.copy()
    if args.target_db:
        env["CONTEXTKEEP_DB_PATH"] = str(args.target_db)

    if args.v1_source:
        migration = [
            sys.executable,
            str(PROJECT_ROOT / "migrate.py"),
            "--source",
            str(args.v1_source),
            "--target",
            str(args.target_db or PROJECT_ROOT / "data" / "contextkeep.db"),
            "--check",
        ]
        run_command(migration, cwd=PROJECT_ROOT, env=env)
        migration.remove("--check")
        if args.reset_target:
            migration.append("--reset-target")
        run_command(migration, cwd=PROJECT_ROOT, env=env)

    run_command([sys.executable, "-m", "compileall", "-q", str(PROJECT_ROOT)], cwd=PROJECT_ROOT, env=env)
    run_command([sys.executable, str(PROJECT_ROOT / "scripts" / "healthcheck.py")], cwd=PROJECT_ROOT, env=env)
    print("Bare-metal V2.1 upgrade checks completed.")
    return 0


def run_docker_upgrade(args: argparse.Namespace) -> int:
    backup = create_docker_backup(
        compose_file=args.compose_file,
        service=args.service,
        volume=args.volume,
        output_dir=args.backup_output_dir,
        helper_image=args.helper_image,
    )
    print_restore_hint(backup, "docker", "")

    compose = docker_compose_command(args.compose_file)
    if not args.no_stop:
        run_command(compose + ["down"], cwd=args.compose_file.parent)
    run_command(compose + ["up", "-d", "--build"], cwd=args.compose_file.parent)
    run_command(compose + ["ps"], cwd=args.compose_file.parent)
    run_command(compose + ["exec", "-T", args.service, "python", "scripts/healthcheck.py"], cwd=args.compose_file.parent)
    print("Docker V2.1 upgrade checks completed.")
    return 0


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely upgrade ContextKeep to V2.1")
    sub = parser.add_subparsers(dest="mode", required=True)

    baremetal = sub.add_parser("baremetal", help="Upgrade a bare-metal install")
    baremetal.add_argument("--install-dir", type=Path, default=PROJECT_ROOT)
    baremetal.add_argument("--backup-output-dir", type=Path, default=PROJECT_ROOT / "backups")
    baremetal.add_argument("--v1-source", type=Path, default=None, help="Optional V1 data/memories folder to migrate")
    baremetal.add_argument("--target-db", type=Path, default=PROJECT_ROOT / "data" / "contextkeep.db")
    baremetal.add_argument("--reset-target", action="store_true", help="Allow migrate.py to rebuild an existing target DB")

    docker = sub.add_parser("docker", help="Upgrade a Docker Compose install")
    docker.add_argument("--compose-file", type=Path, default=PROJECT_ROOT / "docker-compose.yml")
    docker.add_argument("--service", default="contextkeep")
    docker.add_argument("--volume", default="", help="Backup this Docker volume directly instead of using docker cp")
    docker.add_argument("--backup-output-dir", type=Path, default=PROJECT_ROOT / "backups")
    docker.add_argument("--helper-image", default="busybox:1.36")
    docker.add_argument("--no-stop", action="store_true", help="Skip docker compose down before rebuilding")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.mode == "baremetal":
            return run_baremetal_upgrade(args)
        return run_docker_upgrade(args)
    except subprocess.CalledProcessError as exc:
        print(f"Upgrade command failed with exit code {exc.returncode}.", file=sys.stderr)
        return exc.returncode or 1
    except Exception as exc:
        print(f"Upgrade failed before changes could be completed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
