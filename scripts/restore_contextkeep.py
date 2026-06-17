#!/usr/bin/env python3
"""Restore a verified ContextKeep backup."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def prepare_backup(backup: Path, work_dir: Path) -> Path:
    backup = backup.resolve()
    if backup.is_dir():
        return backup
    if backup.suffix.lower() != ".zip":
        raise ValueError("Backup must be a backup folder or .zip archive")
    extract_dir = work_dir / backup.stem
    with zipfile.ZipFile(backup, "r") as archive:
        bad_file = archive.testzip()
        if bad_file:
            raise RuntimeError(f"Backup archive is corrupt at {bad_file}")
        archive.extractall(extract_dir)
    return extract_dir


def load_manifest(backup_dir: Path) -> dict:
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found in backup: {backup_dir}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def copy_tree_contents(source: Path, target: Path) -> None:
    for item in source.iterdir():
        destination = target / item.name
        if item.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(item, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)


def restore_baremetal(backup_dir: Path, target_dir: Path, confirm: bool) -> None:
    if not confirm:
        raise RuntimeError("Refusing to restore without --confirm")
    files_dir = backup_dir / "files"
    if not files_dir.exists():
        raise FileNotFoundError(f"Bare-metal files folder not found in backup: {files_dir}")

    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    rescue_dir = target_dir.parent / f"{target_dir.name}.pre_restore_{timestamp()}"
    if target_dir.exists() and any(target_dir.iterdir()):
        shutil.copytree(target_dir, rescue_dir, ignore=shutil.ignore_patterns(".venv", "venv", "__pycache__"))
        print(f"Created pre-restore safety copy: {rescue_dir}")
    copy_tree_contents(files_dir, target_dir)


def restore_docker_volume(backup_dir: Path, volume: str, helper_image: str, confirm: bool) -> None:
    if not confirm:
        raise RuntimeError("Refusing to restore without --confirm")
    if not volume:
        raise ValueError("--volume is required for Docker volume restore")
    data_dir = backup_dir / "docker_data"
    if not data_dir.exists():
        raise FileNotFoundError(f"Docker data folder not found in backup: {data_dir}")

    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{volume}:/restore_target",
        "-v",
        f"{data_dir.resolve()}:/restore_source:ro",
        helper_image,
        "sh",
        "-c",
        "rm -rf /restore_target/* /restore_target/.[!.]* /restore_target/..?* 2>/dev/null || true; cp -a /restore_source/. /restore_target/",
    ]
    run_command(command)


def restore_docker_container(backup_dir: Path, container: str, confirm: bool) -> None:
    if not confirm:
        raise RuntimeError("Refusing to restore without --confirm")
    if not container:
        raise ValueError("--container is required for Docker container restore")
    data_dir = backup_dir / "docker_data"
    if not data_dir.exists():
        raise FileNotFoundError(f"Docker data folder not found in backup: {data_dir}")
    run_command(["docker", "cp", str(data_dir / "."), f"{container}:/app/data"])


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore a ContextKeep backup")
    sub = parser.add_subparsers(dest="mode", required=True)

    baremetal = sub.add_parser("baremetal", help="Restore a bare-metal backup to an install folder")
    baremetal.add_argument("--backup", type=Path, required=True)
    baremetal.add_argument("--target-dir", type=Path, required=True)
    baremetal.add_argument("--confirm", action="store_true")

    docker = sub.add_parser("docker", help="Restore a Docker backup to a volume or container")
    docker.add_argument("--backup", type=Path, required=True)
    docker.add_argument("--volume", default="")
    docker.add_argument("--container", default="")
    docker.add_argument("--helper-image", default="busybox:1.36")
    docker.add_argument("--confirm", action="store_true")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="contextkeep_restore_") as tmp:
        try:
            backup_dir = prepare_backup(args.backup, Path(tmp))
            manifest = load_manifest(backup_dir)
            if args.mode != manifest.get("mode"):
                raise RuntimeError(
                    f"Backup mode is {manifest.get('mode')!r}, but restore mode is {args.mode!r}"
                )
            if args.mode == "baremetal":
                restore_baremetal(backup_dir, args.target_dir, args.confirm)
            elif args.volume:
                restore_docker_volume(backup_dir, args.volume, args.helper_image, args.confirm)
            else:
                restore_docker_container(backup_dir, args.container, args.confirm)
            print("ContextKeep restore complete.")
            return 0
        except Exception as exc:
            print(f"Restore failed: {exc}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
