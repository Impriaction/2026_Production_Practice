#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import annotations

import argparse
import logging
import shutil
import stat
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from od_platform.common.audit_utils import (
    build_audit_payload,
    create_backup_archive,
    summarize_paths,
    write_audit_log,
)
from od_platform.common.logging_utils import get_logger
from od_platform.common.paths import (
    APP_DIR,
    DATA_DIR,
    LOGGING_DIR,
    META_LOGGING_DIR,
    MODELS_DIR,
    RAW_DATA_DIR,
    RESET_AUDIT_DIR,
    RESET_BACKUPS_DIR,
    ROOT_DIR,
    get_dirs_to_reset,
    get_protected_reset_paths,
    is_protected_reset_path,
)
from od_platform.common.performance_utils import time_it
from od_platform.common.string_utils import format_table_row, format_table_separator

DEFAULT_SCOPE = "runtime"
SCOPE_CHOICES = ("runtime", "runtime-plus-raw", "full")
LARGE_SIZE_WARNING_BYTES = 1024 * 1024 * 1024
LARGE_FILE_COUNT_WARNING = 10000
LINE_WIDTH = 72

SCOPE_MENU = {
    "1": {
        "scope": "runtime",
        "title": "Runtime Reset",
        "summary": "Only delete generated runtime artifacts.",
        "targets": "runs, models/trained, data/processed, apps/platform/logging",
        "risk": "Low",
    },
    "2": {
        "scope": "runtime-plus-raw",
        "title": "Runtime + Raw Data Reset",
        "summary": "Delete runtime artifacts and raw dataset contents.",
        "targets": "runtime targets + data/raw",
        "risk": "Medium",
    },
    "3": {
        "scope": "full",
        "title": "Full Data Reset",
        "summary": "Delete almost all generated data content except protected paths.",
        "targets": "runtime targets + raw + extra data/models children",
        "risk": "High (requires --force)",
    },
}

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odp-reset",
        description="Preview or reset generated project artifacts safely.",
    )
    parser.add_argument(
        "--scope",
        choices=SCOPE_CHOICES,
        default=DEFAULT_SCOPE,
        help="Reset scope. Default only clears runtime artifacts.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the reset. Without this flag, only preview.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force preview mode even if --execute is supplied elsewhere.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip interactive confirmation prompts.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Required for the high-risk full scope reset.",
    )
    return parser


def _deduplicate_paths(paths: Iterable[Path]) -> List[Path]:
    seen: set[str] = set()
    result: List[Path] = []
    for path in paths:
        key = str(path.resolve())
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def _expand_full_scope_targets(base_targets: Iterable[Path]) -> List[Path]:
    expanded: List[Path] = []
    protected_paths = get_protected_reset_paths()
    for path in base_targets:
        if path in (DATA_DIR, MODELS_DIR):
            if not path.exists():
                continue
            for child in sorted(path.iterdir()):
                if not is_protected_reset_path(child, protected_paths):
                    expanded.append(child)
            continue
        expanded.append(path)
    return _deduplicate_paths(expanded)


def _resolve_targets(scope: str) -> List[Path]:
    base_targets = get_dirs_to_reset(scope)
    if scope == "full":
        return _expand_full_scope_targets(base_targets)
    return _deduplicate_paths(base_targets)


def _find_unsafe_targets(targets: Iterable[Path]) -> List[Path]:
    protected_paths = get_protected_reset_paths()
    return [path for path in targets if is_protected_reset_path(path, protected_paths)]


def _render_scope_menu(current_scope: str) -> None:
    border = "=" * LINE_WIDTH
    print(border)
    print("ODPlatform Reset Scope Menu".center(LINE_WIDTH))
    print(border)
    print(f"Current default: {current_scope}")
    print("Choose the reset range before execution:\n")
    for key, item in SCOPE_MENU.items():
        selected = " (default)" if item["scope"] == current_scope else ""
        print(f"{key}. {item['title']}{selected}")
        print(f"   Scope   : {item['scope']}")
        print(f"   Summary : {item['summary']}")
        print(f"   Targets : {item['targets']}")
        print(f"   Risk    : {item['risk']}")
        print("-" * LINE_WIDTH)
    print("Press Enter to keep the current default.")


def _choose_scope_interactively(current_scope: str) -> str:
    if not sys.stdin.isatty():
        return current_scope
    _render_scope_menu(current_scope)
    while True:
        answer = input(f"Select scope [1/2/3, Enter={current_scope}]: ").strip()
        if not answer:
            return current_scope
        if answer in SCOPE_MENU:
            selected_scope = SCOPE_MENU[answer]["scope"]
            print(f"Selected scope: {selected_scope}")
            return selected_scope
        print("Invalid selection. Please enter 1, 2, 3, or press Enter.")


def _warn_if_risky(summary: dict) -> None:
    if summary["total_bytes"] >= LARGE_SIZE_WARNING_BYTES:
        logger.warning("Large cleanup size detected: %s", summary["display_total_size"])
    if summary["total_files"] >= LARGE_FILE_COUNT_WARNING:
        logger.warning("Large file count detected: %s", summary["total_files"])


def _display_path(item_path: str) -> str:
    path = Path(item_path)
    if str(path).startswith(str(ROOT_DIR)):
        try:
            return str(path.relative_to(ROOT_DIR))
        except ValueError:
            return item_path
    return item_path


def _log_preview(scope: str, dry_run: bool, summary: dict) -> None:
    logger.info("Reset Preview".center(LINE_WIDTH, "="))
    logger.info("Project root : %s", ROOT_DIR)
    logger.info("Scope        : %s", scope)
    logger.info("Mode         : %s", "dry-run" if dry_run else "execute")
    logger.info("Backup dir   : %s", RESET_BACKUPS_DIR.relative_to(ROOT_DIR))
    logger.info("Audit dir    : %s", RESET_AUDIT_DIR.relative_to(ROOT_DIR))

    widths = [38, 8, 8, 12]
    aligns = ["left", "right", "right", "right"]
    logger.info(format_table_row(["Path", "Files", "Dirs", "Size"], widths, aligns))
    logger.info(format_table_separator(widths))
    for item in summary["items"]:
        logger.info(
            format_table_row(
                [
                    _display_path(item["path"]),
                    str(item["files"]),
                    str(item["dirs"]),
                    item["display_size"],
                ],
                widths,
                aligns,
            )
        )
    logger.info(format_table_separator(widths))
    logger.info(
        format_table_row(
            ["Total", str(summary["total_files"]), str(summary["total_dirs"]), summary["display_total_size"]],
            widths,
            aligns,
        )
    )
    _warn_if_risky(summary)


def _confirm_execution(scope: str, summary: dict) -> bool:
    if not sys.stdin.isatty():
        return False
    print()
    print("=" * LINE_WIDTH)
    print("About to execute a real reset")
    print(f"Scope      : {scope}")
    print(f"Total size : {summary['display_total_size']}")
    print(f"Files      : {summary['total_files']}")
    print(f"Dirs       : {summary['total_dirs']}")
    print("=" * LINE_WIDTH)
    first = input("Type yes to continue, or anything else to cancel: ").strip().lower()
    if first != "yes":
        return False
    second = input("Type RESET to confirm deletion: ").strip()
    return second == "RESET"


def _handle_remove_readonly(func, path, exc_info) -> None:
    del exc_info
    os_path = Path(path)
    os_path.chmod(stat.S_IWRITE)
    func(path)


def _delete_target(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        return

    if path.is_file():
        path.chmod(stat.S_IWRITE)
        path.unlink()
        return

    shutil.rmtree(path, onerror=_handle_remove_readonly)
    path.mkdir(parents=True, exist_ok=True)


def _validate_args(args: argparse.Namespace) -> None:
    if args.scope == "full" and not args.force:
        raise ValueError("full scope requires --force")


@time_it(name="reset_project", logger_instance=logger)
def _run_reset(scope: str, dry_run: bool, skip_confirm: bool) -> int:
    targets = _resolve_targets(scope)
    unsafe_targets = _find_unsafe_targets(targets)
    if unsafe_targets:
        for path in unsafe_targets:
            logger.error("Protected path detected, refusing to reset: %s", path)
        return 2

    summary = summarize_paths(targets)
    _log_preview(scope, dry_run, summary)

    if dry_run:
        audit_path = write_audit_log(
            RESET_AUDIT_DIR,
            build_audit_payload(
                mode="preview",
                scope=scope,
                dry_run=True,
                targets=targets,
                summary=summary,
                backup_archive=None,
            ),
        )
        logger.info("Dry-run completed. Audit record: %s", audit_path)
        return 0

    if not skip_confirm and not _confirm_execution(scope, summary):
        logger.warning("Reset execution cancelled by user.")
        audit_path = write_audit_log(
            RESET_AUDIT_DIR,
            build_audit_payload(
                mode="cancelled",
                scope=scope,
                dry_run=False,
                targets=targets,
                summary=summary,
                backup_archive=None,
            ),
        )
        logger.info("Cancellation audit recorded: %s", audit_path)
        return 3

    backup_archive = create_backup_archive(targets, ROOT_DIR, RESET_BACKUPS_DIR, scope)
    logger.info("Backup created: %s", backup_archive)

    deleted_paths: List[Path] = []
    errors: List[str] = []
    for target in targets:
        try:
            logger.info("Resetting: %s", target.relative_to(ROOT_DIR))
            _delete_target(target)
            deleted_paths.append(target)
        except OSError as exc:
            error_message = f"{target}: {exc}"
            logger.error("Reset failed: %s", error_message)
            errors.append(error_message)

    audit_path = write_audit_log(
        RESET_AUDIT_DIR,
        build_audit_payload(
            mode="execute" if not errors else "failed",
            scope=scope,
            dry_run=False,
            targets=targets,
            summary=summary,
            backup_archive=backup_archive,
            deleted_paths=deleted_paths,
            errors=errors,
        ),
    )
    logger.info("Reset audit completed: %s", audit_path)

    if errors:
        return 1
    logger.info("Reset completed".center(LINE_WIDTH, "="))
    return 0


def reset_project(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    scope = args.scope
    if args.execute and not args.yes:
        scope = _choose_scope_interactively(scope)
    dry_run = True if args.dry_run else not args.execute

    get_logger(
        base_path=RESET_AUDIT_DIR,
        log_type="reset_project",
        temp_log=False,
    )

    logger.info("App dir      : %s", APP_DIR)
    logger.info("Logging dir  : %s", LOGGING_DIR)
    logger.info("Meta log dir : %s", META_LOGGING_DIR)

    try:
        _validate_args(argparse.Namespace(scope=scope, force=args.force))
    except ValueError as exc:
        logger.error("%s", exc)
        return 2

    return _run_reset(scope=scope, dry_run=dry_run, skip_confirm=args.yes)


def main() -> None:
    raise SystemExit(reset_project())


if __name__ == "__main__":
    main()
