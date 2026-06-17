#!/usr/bin/env python3
"""Create verified ContextKeep backups before an upgrade.

The script uses only Python's standard library so it can run before project
dependencies are installed. Backups are staged as normal files, validated, and
then packed into a ZIP archive whose contents are checksum-verified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


APP_VERSION = "2.1.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "backups"
DB_SUFFIXES = {".db", ".sqlite", ".sqlite3"}
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "__pycache__",
    "backups",
    "backups_test",
    "restore_test",
}
SKIP_SUFFIXES = {".pyc", ".pyo", ".db-wal", ".db-shm"}


@dataclass
class BackupResult:
    mode: str
    backup_dir: Path
    archive_path: Path
    manifest_path: Path
    file_count: int


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(command: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in SKIP_DIRS for part in rel.parts):
        return True
    name = path.name
    if any(name.endswith(suffix) for suffix in SKIP_SUFFIXES):
        return True
    return False


def is_sqlite_database(path: Path) -> bool:
    if path.suffix.lower() not in DB_SUFFIXES:
        return False
    if not path.exists() or path.stat().st_size < 16:
        return False
    with path.open("rb") as handle:
        return handle.read(16) == b"SQLite format 3\x00"


def sqlite_integrity_check(path: Path) -> None:
    if not is_sqlite_database(path):
        return
    uri = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise RuntimeError(f"SQLite integrity check failed for {path}: {result[0] if result else 'no result'}")
    finally:
        conn.close()


def copy_sqlite_snapshot(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_uri = f"file:{source.as_posix()}?mode=ro"
    src = sqlite3.connect(source_uri, uri=True)
    try:
        dst = sqlite3.connect(str(destination))
        try:
            src.backup(dst)
            dst.commit()
        finally:
            dst.close()
    finally:
        src.close()
    sqlite_integrity_check(destination)


def is_inside_any(path: Path, roots: Iterable[Path]) -> bool:
    resolved = path.resolve()
    for root in roots:
        root = root.resolve()
        if resolved == root or resolved.is_relative_to(root):
            return True
    return False


def copy_install_tree(
    source_root: Path,
    destination_root: Path,
    skip_roots: Iterable[Path] = (),
) -> list[str]:
    copied: list[str] = []
    for path in sorted(source_root.rglob("*")):
        if is_inside_any(path, skip_roots):
            continue
        if should_skip(path, source_root):
            continue
        rel = path.relative_to(source_root)
        target = destination_root / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if is_sqlite_database(path):
            sqlite_integrity_check(path)
            copy_sqlite_snapshot(path, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        copied.append(rel.as_posix())
    return copied


def validate_json_memories(root: Path) -> list[str]:
    checked: list[str] = []
    for folder in root.rglob("memories"):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle)
            checked.append(path.relative_to(root).as_posix())
    return checked


def validate_backup_tree(root: Path) -> dict[str, Any]:
    sqlite_checked: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and is_sqlite_database(path):
            sqlite_integrity_check(path)
            sqlite_checked.append(path.relative_to(root).as_posix())
    json_checked = validate_json_memories(root)
    return {
        "sqlite_integrity_checked": sqlite_checked,
        "json_memories_checked": json_checked,
    }


def build_manifest(
    mode: str,
    source: str,
    backup_root: Path,
    checks: dict[str, Any],
    docker: dict[str, Any] | None = None,
) -> dict[str, Any]:
    files = []
    for path in sorted(backup_root.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        rel = path.relative_to(backup_root).as_posix()
        files.append(
            {
                "path": rel,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "backup_format": 1,
        "created_at": utc_now(),
        "created_by": f"ContextKeep {APP_VERSION}",
        "mode": mode,
        "source": source,
        "docker": docker or {},
        "checks": checks,
        "files": files,
    }


def write_restore_notes(backup_root: Path, mode: str) -> None:
    notes = [
        "# ContextKeep Backup Restore Notes",
        "",
        "This backup was created before a ContextKeep upgrade and was verified before the upgrade continued.",
        "",
        "Use the restore helper from the same ContextKeep release:",
        "",
    ]
    if mode == "docker":
        notes.extend(
            [
                "```bash",
                "python scripts/restore_contextkeep.py docker --backup <backup-zip-or-folder> --volume <docker-volume-name> --confirm",
                "```",
                "",
                "Stop the ContextKeep container before restoring a Docker volume.",
            ]
        )
    else:
        notes.extend(
            [
                "```bash",
                "python scripts/restore_contextkeep.py baremetal --backup <backup-zip-or-folder> --target-dir <install-dir> --confirm",
                "```",
                "",
                "Stop the ContextKeep server and WebUI before restoring a bare-metal install.",
            ]
        )
    (backup_root / "RESTORE_INSTRUCTIONS.md").write_text("\n".join(notes) + "\n", encoding="utf-8")


def zip_directory(source_dir: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir).as_posix())


def verify_archive(archive_path: Path, manifest: dict[str, Any]) -> None:
    expected = {item["path"]: item for item in manifest["files"]}
    with zipfile.ZipFile(archive_path, "r") as archive:
        bad_file = archive.testzip()
        if bad_file:
            raise RuntimeError(f"ZIP verification failed at {bad_file}")
        for rel, item in expected.items():
            with archive.open(rel, "r") as handle:
                digest = hashlib.sha256()
                size = 0
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
                    size += len(chunk)
            if size != item["size"] or digest.hexdigest() != item["sha256"]:
                raise RuntimeError(f"Checksum mismatch inside archive: {rel}")


def create_baremetal_backup(install_dir: Path, output_dir: Path = DEFAULT_OUTPUT_DIR) -> BackupResult:
    install_dir = install_dir.resolve()
    if not install_dir.exists() or not install_dir.is_dir():
        raise FileNotFoundError(f"Install directory not found: {install_dir}")

    name = f"contextkeep_baremetal_backup_{timestamp()}"
    backup_dir = (output_dir / name).resolve()
    files_root = backup_dir / "files"
    backup_dir.mkdir(parents=True, exist_ok=True)

    copied = copy_install_tree(install_dir, files_root, skip_roots=[output_dir])
    checks = validate_backup_tree(files_root)
    checks["copied_files"] = len(copied)
    write_restore_notes(backup_dir, "baremetal")
    checks = validate_backup_tree(backup_dir)
    checks["copied_files"] = len(copied)

    manifest = build_manifest("baremetal", str(install_dir), backup_dir, checks)
    manifest_path = backup_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    archive_path = output_dir / f"{name}.zip"
    zip_directory(backup_dir, archive_path)
    verify_archive(archive_path, manifest)
    return BackupResult("baremetal", backup_dir, archive_path, manifest_path, len(manifest["files"]))


def docker_compose_base(compose_file: Path | None) -> list[str]:
    command = ["docker", "compose"]
    if compose_file:
        command.extend(["-f", str(compose_file)])
    return command


def docker_ps(compose_file: Path | None, service: str = "") -> list[str]:
    command = docker_compose_base(compose_file) + ["ps", "-q"]
    if service:
        command.append(service)
    result = run_command(command, check=False)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def docker_ps_by_name(name: str = "contextkeep") -> list[str]:
    result = run_command(
        ["docker", "ps", "-a", "--filter", f"name={name}", "--format", "{{.ID}}"],
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def docker_inspect(container_id: str) -> dict[str, Any]:
    result = run_command(["docker", "inspect", container_id])
    data = json.loads(result.stdout)
    if not data:
        raise RuntimeError(f"docker inspect returned no data for {container_id}")
    return data[0]


def discover_data_container(compose_file: Path | None, service: str = "") -> tuple[str, dict[str, Any]]:
    candidates = docker_ps(compose_file, service)
    if not candidates and service:
        candidates = docker_ps(compose_file, "")
    if not candidates:
        candidates = docker_ps_by_name("contextkeep")
    for container_id in candidates:
        data = docker_inspect(container_id)
        for mount in data.get("Mounts", []):
            if mount.get("Destination") == "/app/data":
                return container_id, data
    if candidates:
        return candidates[0], docker_inspect(candidates[0])
    raise RuntimeError("No Docker Compose containers found. Start the existing stack or pass --volume.")


def copy_docker_volume_with_busybox(volume: str, destination: Path, image: str) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{volume}:/source:ro",
        "-v",
        f"{destination.resolve()}:/backup",
        image,
        "sh",
        "-c",
        "cp -a /source/. /backup/",
    ]
    run_command(command)


def copy_docker_data_from_container(container_id: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    result = run_command(["docker", "cp", f"{container_id}:/app/data", str(destination)], check=False)
    if result.returncode != 0:
        raise RuntimeError(f"docker cp failed: {result.stderr.strip()}")


def create_docker_backup(
    compose_file: Path | None = None,
    service: str = "contextkeep",
    volume: str = "",
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    helper_image: str = "busybox:1.36",
) -> BackupResult:
    compose_file = compose_file.resolve() if compose_file else None
    name = f"contextkeep_docker_backup_{timestamp()}"
    backup_dir = (output_dir / name).resolve()
    docker_data = backup_dir / "docker_data"
    compose_root = backup_dir / "compose"
    backup_dir.mkdir(parents=True, exist_ok=True)

    docker_meta: dict[str, Any] = {
        "compose_file": str(compose_file) if compose_file else "",
        "service": service,
        "volume": volume,
    }

    if compose_file and compose_file.exists():
        compose_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(compose_file, compose_root / compose_file.name)
        env_file = compose_file.parent / ".env"
        if env_file.exists():
            shutil.copy2(env_file, compose_root / ".env")

    if volume:
        copy_docker_volume_with_busybox(volume, docker_data, helper_image)
    else:
        container_id, inspect_data = discover_data_container(compose_file, service)
        docker_meta["container_id"] = container_id
        docker_meta["image"] = inspect_data.get("Config", {}).get("Image", "")
        docker_meta["mounts"] = inspect_data.get("Mounts", [])
        copy_docker_data_from_container(container_id, docker_data)

    checks = validate_backup_tree(backup_dir)
    write_restore_notes(backup_dir, "docker")
    checks = validate_backup_tree(backup_dir)
    manifest = build_manifest("docker", str(compose_file or volume or "docker"), backup_dir, checks, docker_meta)
    manifest_path = backup_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    archive_path = output_dir / f"{name}.zip"
    zip_directory(backup_dir, archive_path)
    verify_archive(archive_path, manifest)
    return BackupResult("docker", backup_dir, archive_path, manifest_path, len(manifest["files"]))


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create verified backups for ContextKeep upgrades")
    sub = parser.add_subparsers(dest="mode", required=True)

    baremetal = sub.add_parser("baremetal", help="Back up a bare-metal ContextKeep install folder")
    baremetal.add_argument("--install-dir", type=Path, default=PROJECT_ROOT)
    baremetal.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)

    docker = sub.add_parser("docker", help="Back up a Docker Compose ContextKeep install")
    docker.add_argument("--compose-file", type=Path, default=PROJECT_ROOT / "docker-compose.yml")
    docker.add_argument("--service", default="contextkeep")
    docker.add_argument("--volume", default="", help="Backup this Docker volume directly instead of using docker cp")
    docker.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    docker.add_argument("--helper-image", default="busybox:1.36")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.mode == "baremetal":
            result = create_baremetal_backup(args.install_dir, args.output_dir)
        else:
            result = create_docker_backup(
                compose_file=args.compose_file,
                service=args.service,
                volume=args.volume,
                output_dir=args.output_dir,
                helper_image=args.helper_image,
            )
        print("Verified ContextKeep backup created.")
        print(f"  Mode: {result.mode}")
        print(f"  Backup folder: {result.backup_dir}")
        print(f"  Archive: {result.archive_path}")
        print(f"  Manifest: {result.manifest_path}")
        print(f"  Files verified: {result.file_count}")
        return 0
    except Exception as exc:
        print(f"Backup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
