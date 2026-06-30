from __future__ import annotations

import getpass
import json
import socket
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


def format_bytes(size_in_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_in_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024
    return f"{size_in_bytes} B"


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def ensure_audit_directories(*directories: Path) -> None:
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def collect_path_stats(path: Path) -> Dict[str, Any]:
    stats = {
        "path": path,
        "exists": path.exists(),
        "files": 0,
        "dirs": 0,
        "bytes": 0,
    }
    if not path.exists():
        return stats

    if path.is_file():
        stats["files"] = 1
        stats["bytes"] = path.stat().st_size
        return stats

    stats["dirs"] = 1
    for child in path.rglob("*"):
        if child.is_dir():
            stats["dirs"] += 1
        elif child.is_file():
            stats["files"] += 1
            stats["bytes"] += child.stat().st_size
    return stats


def summarize_paths(paths: Iterable[Path]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    total_files = 0
    total_dirs = 0
    total_bytes = 0

    for path in paths:
        item = collect_path_stats(path)
        item["display_size"] = format_bytes(item["bytes"])
        item["path"] = str(item["path"])
        items.append(item)
        total_files += item["files"]
        total_dirs += item["dirs"]
        total_bytes += item["bytes"]

    return {
        "items": items,
        "total_files": total_files,
        "total_dirs": total_dirs,
        "total_bytes": total_bytes,
        "display_total_size": format_bytes(total_bytes),
    }


def create_backup_archive(
    targets: Iterable[Path],
    root_dir: Path,
    backup_root: Path,
    scope: str,
) -> Path:
    ensure_audit_directories(backup_root)
    archive_path = backup_root / f"reset-{scope}-{timestamp_slug()}.zip"

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for target in targets:
            if not target.exists():
                continue
            if target.is_file():
                archive.write(target, arcname=str(target.relative_to(root_dir)))
                continue
            for child in target.rglob("*"):
                if child.is_file():
                    archive.write(child, arcname=str(child.relative_to(root_dir)))

    return archive_path


def build_audit_payload(
    *,
    mode: str,
    scope: str,
    dry_run: bool,
    targets: Iterable[Path],
    summary: Dict[str, Any],
    backup_archive: Path | None,
    deleted_paths: Iterable[Path] | None = None,
    errors: Iterable[str] | None = None,
) -> Dict[str, Any]:
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "scope": scope,
        "dry_run": dry_run,
        "user": getpass.getuser(),
        "host": socket.gethostname(),
        "targets": [str(path) for path in targets],
        "summary": summary,
        "backup_archive": str(backup_archive) if backup_archive else None,
        "deleted_paths": [str(path) for path in (deleted_paths or [])],
        "errors": list(errors or []),
    }


def write_audit_log(audit_root: Path, payload: Dict[str, Any]) -> Path:
    ensure_audit_directories(audit_root)
    audit_path = audit_root / f"reset-audit-{timestamp_slug()}.json"
    audit_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return audit_path
