#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : reset_project.py
# @Author    : ODPlatform team
# @Project   : ODPlatform
# @Function  : Project reset tool

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import getpass

from od_platform.common.logging_utils import get_logger
from od_platform.common.paths import (
    LOGGING_DIR,
    PRETRAINED_MODELS_DIR,
    RAW_DATA_DIR,
    ROOT_DIR,
    get_dirs_to_reset,
    is_protected,
)
from od_platform.common.string_utils import format_table_row, format_table_separator

logger = get_logger(
    base_path=LOGGING_DIR,
    log_type="reset_project",
    temp_log=False,
)

CONFIRM_KEYWORD = "RESET"
LINE_WIDTH = 70


def _format_size(bytes_size: int) -> str:
    if bytes_size >= 1024**3:
        return f"{bytes_size / (1024**3):.2f} GiB"
    if bytes_size >= 1024**2:
        return f"{bytes_size / (1024**2):.2f} MiB"
    if bytes_size >= 1024:
        return f"{bytes_size / 1024:.2f} KiB"
    return f"{bytes_size} B"


def _on_rm_error(func, path, exc_info) -> None:
    del exc_info
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _audit_context() -> dict:
    try:
        git_rev = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        git_rev = "(not a git repo)"

    return {
        "user": getpass.getuser(),
        "pid": os.getpid(),
        "git_rev": git_rev,
        "argv": sys.argv,
        "cwd": os.getcwd(),
    }


def _scan_targets() -> tuple[list[tuple[Path, int, int]], list[Path]]:
    deletable: list[tuple[Path, int, int]] = []
    skipped: list[Path] = []

    for directory in get_dirs_to_reset():
        if is_protected(directory):
            logger.warning("Refuse to reset protected directory: %s", directory)
            skipped.append(directory)
            continue

        if not directory.exists():
            skipped.append(directory)
            continue

        file_count = 0
        total_size = 0
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    file_count += 1
                    try:
                        total_size += item.stat().st_size
                    except OSError:
                        pass
        except OSError as exc:
            logger.warning("Failed while scanning %s: %s", directory, exc)

        deletable.append((directory, file_count, total_size))

    return deletable, skipped


def _print_plan(
    deletable: list[tuple[Path, int, int]],
    skipped: list[Path],
    will_actually_delete: bool,
) -> None:
    del skipped

    title = "Directories to delete" if will_actually_delete else "[DRY-RUN] Planned reset"
    logger.info(title.center(LINE_WIDTH, "="))

    if not deletable:
        logger.info("No deletable directories found. Project is already clean.")
        return

    widths = [40, 12, 14]
    aligns = ["left", "right", "right"]
    logger.info(format_table_row(["Directory", "Files", "Size"], widths, aligns))
    logger.info(format_table_separator(widths))

    total_files = 0
    total_bytes = 0
    for path, count, size in deletable:
        rel = path.relative_to(ROOT_DIR)
        logger.info(
            format_table_row([str(rel), str(count), _format_size(size)], widths, aligns)
        )
        total_files += count
        total_bytes += size

    logger.info(format_table_separator(widths))
    logger.info(
        format_table_row(["[Total]", str(total_files), _format_size(total_bytes)], widths, aligns)
    )
    logger.info("")
    logger.info("Protected directories that will NOT be touched:")
    logger.info("  - Raw data: %s/", RAW_DATA_DIR.relative_to(ROOT_DIR))
    logger.info("  - Pretrained weights: %s/", PRETRAINED_MODELS_DIR.relative_to(ROOT_DIR))
    logger.info("  - Source code, docs, scripts, git metadata")


def _confirm(deletable_count: int) -> bool:
    print()
    print("=" * LINE_WIDTH)
    print(f"You are about to delete the contents of {deletable_count} directories.")
    print(f"Type the exact keyword '{CONFIRM_KEYWORD}' to continue.")
    print("Any other input will cancel the operation.")
    print("=" * LINE_WIDTH)
    try:
        user_input = input("> ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return False
    return user_input == CONFIRM_KEYWORD


def _delete_one(path: Path, idx: int, total: int, file_count: int, size: int) -> str | None:
    if is_protected(path):
        logger.error("[%s/%s] Skip protected directory: %s", idx, total, path)
        return "protected directory"

    rel = path.relative_to(ROOT_DIR)
    size_str = _format_size(size)
    logger.info("[%s/%s] Deleting %s (%s, %s files)", idx, total, rel, size_str, file_count)

    try:
        shutil.rmtree(path, onerror=_on_rm_error)
        logger.info("[%s/%s] Deleted %s", idx, total, rel)
        return None
    except OSError as exc:
        logger.error("[%s/%s] Failed to delete %s: %s", idx, total, rel, exc)
        return str(exc)


def _execute_delete(deletable: list[tuple[Path, int, int]]) -> None:
    total = len(deletable)
    success: list[Path] = []
    failed: list[tuple[Path, str]] = []

    for idx, (path, file_count, size) in enumerate(deletable, 1):
        reason = _delete_one(path, idx, total, file_count, size)
        if reason is None:
            success.append(path)
        else:
            failed.append((path, reason))

    logger.info("=" * LINE_WIDTH)
    if failed:
        logger.warning("Finished: success %s, failed %s", len(success), len(failed))
        for path, reason in failed:
            logger.warning("  - %s: %s", path.relative_to(ROOT_DIR), reason)
    else:
        logger.info("Finished: success %s, failed 0", len(success))


def reset_project(yes: bool = False, force: bool = False, dry_run: bool = False) -> int:
    logger.info("Project reset tool".center(LINE_WIDTH, "="))
    logger.info("Project root: %s", ROOT_DIR)

    ctx = _audit_context()
    logger.info("Audit: user=%s, pid=%s, git=%s", ctx["user"], ctx["pid"], ctx["git_rev"])
    logger.info("Audit: cwd=%s", ctx["cwd"])
    logger.info("Audit: argv=%s", " ".join(ctx["argv"]))

    if dry_run and yes:
        logger.warning("Both --dry-run and --yes were provided. Using dry-run mode.")
        yes = False

    deletable, skipped = _scan_targets()
    _print_plan(deletable, skipped, will_actually_delete=yes)

    if not deletable:
        return 0

    if not yes:
        logger.info("")
        if dry_run:
            logger.info("This is an explicit --dry-run. To actually delete, add --yes:")
        else:
            logger.info("This is dry-run by default. To actually delete, add --yes:")
        logger.info("   python scripts/reset_project.py --yes")
        return 0

    if not force and not _confirm(len(deletable)):
        logger.warning("Cancelled by user. No files were deleted.")
        return 1

    logger.info("")
    logger.info("Start deleting".center(LINE_WIDTH, "="))
    _execute_delete(deletable)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reset ODPlatform by removing generated runtime artifacts."
    )
    parser.add_argument("--yes", action="store_true", help="Actually perform deletion.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip interactive confirmation. Only meaningful with --yes.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Explicit dry-run mode.")
    args = parser.parse_args()
    return reset_project(yes=args.yes, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
