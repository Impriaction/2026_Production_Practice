from __future__ import annotations

from typing import Any

import yaml

from od_platform.validate_dataset.registry import CheckContext, CheckResult, CheckSeverity


def load_yaml_doc_or_error(ctx: CheckContext, check_name: str) -> tuple[dict[str, Any] | None, CheckResult | None]:
    try:
        return ctx.yaml_doc, None
    except FileNotFoundError:
        return None, CheckResult(
            name=check_name,
            severity=CheckSeverity.ERROR,
            summary=f"yaml 文件不存在: {ctx.yaml_path}",
            details={"reason": "file_not_found", "yaml_path": str(ctx.yaml_path)},
        )
    except yaml.YAMLError as exc:
        return None, CheckResult(
            name=check_name,
            severity=CheckSeverity.ERROR,
            summary=f"yaml 文件解析失败: {exc}",
            details={
                "reason": "parse_error",
                "yaml_path": str(ctx.yaml_path),
                "parser_error": str(exc),
            },
        )
    except OSError as exc:
        return None, CheckResult(
            name=check_name,
            severity=CheckSeverity.ERROR,
            summary=f"yaml 文件读取失败: {exc}",
            details={
                "reason": "read_error",
                "yaml_path": str(ctx.yaml_path),
                "os_error": str(exc),
            },
        )
    except ValueError as exc:
        return None, CheckResult(
            name=check_name,
            severity=CheckSeverity.ERROR,
            summary=f"yaml 结构不合法: {exc}",
            details={"reason": "yaml_structure_error", "yaml_path": str(ctx.yaml_path)},
        )


def load_snapshot_or_error(ctx: CheckContext, check_name: str):
    _, yaml_error = load_yaml_doc_or_error(ctx, check_name)
    if yaml_error is not None:
        return None, yaml_error

    try:
        return ctx.split_snapshot, None
    except ValueError as exc:
        return None, CheckResult(
            name=check_name,
            severity=CheckSeverity.ERROR,
            summary=f"yaml 数据集路径字段不合法: {exc}",
            details={"reason": "path_resolution_error", "yaml_path": str(ctx.yaml_path)},
        )
