#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :yaml_schema.py
# @Time      :2026/7/2 13:01:52
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :
"""
yaml_schema check: 验证数据集 yaml 文件的字段完整性和一致性

检查项: 任意一项失败都要标记 ERROR
    1. yaml 文件存在而且要能解析
    2. yaml 文件的顶层必须是一个字典
    3. 包含 nc 字段, 且是正整数
    4. 包含 names 字段, 且是字符串列表, 或者是一个字典
    5. nc 字段的值等于 names 字段中元素个数
"""

from __future__ import annotations

from typing import Any

import yaml

from od_platform.validate_dataset.registry import (
    CheckContext,
    CheckResult,
    CheckSeverity,
    check,
)


@check("yaml_schema")
def validate_yaml_schema(ctx: CheckContext) -> CheckResult:
    yaml_path = ctx.yaml_path

    if not yaml_path.exists():
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary=f"yaml 文件不存在: {yaml_path}",
            details={"reason": "file_not_found", "yaml_path": str(yaml_path)},
        )

    try:
        with yaml_path.open("r", encoding="utf-8") as file:
            cfg = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary=f"yaml 文件解析失败: {exc}",
            details={
                "reason": "parse_error",
                "yaml_path": str(yaml_path),
                "parser_error": str(exc),
            },
        )
    except OSError as exc:
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary=f"yaml 文件读取失败: {exc}",
            details={
                "reason": "read_error",
                "yaml_path": str(yaml_path),
                "os_error": str(exc),
            },
        )

    if not isinstance(cfg, dict):
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary=f"yaml 文件的顶层不是字典: {type(cfg).__name__}",
            details={"reason": "not_dict", "actual_type": type(cfg).__name__},
        )

    problems: list[str] = []

    nc = cfg.get("nc")
    if not isinstance(nc, int) or nc <= 0:
        problems.append(f"nc 字段不存在或者不是正整数: {nc}")
        nc = None

    names_raw = cfg.get("names")
    names_count, names_problem = _validate_names(names_raw)
    if names_problem:
        problems.append(names_problem)

    if nc is not None and names_count is not None and nc != names_count:
        problems.append(
            f"nc 字段的值({nc})与 names 字段中元素个数({names_count})不相等"
        )

    if problems:
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary=f"yaml 文件字段不一致: {len(problems)} 处问题",
            details={
                "reason": "field_inconsistency",
                "problems": problems,
                "nc": nc,
                "names_count": names_count,
            },
        )

    return CheckResult(
        name="yaml_schema",
        severity=CheckSeverity.INFO,
        summary=f"yaml 文件字段一致 (nc={nc}, names_count={names_count})",
        details={"nc": nc, "names_count": names_count},
    )


def _validate_names(names_raw: Any) -> tuple[int | None, str]:
    if isinstance(names_raw, list):
        if not names_raw:
            return None, "names 是空列表"
        if not all(isinstance(name, str) and name for name in names_raw):
            return None, "names 列表中包含非字符串元素"
        return len(names_raw), ""

    if isinstance(names_raw, dict):
        if not names_raw:
            return None, "names 是空字典"
        if not all(isinstance(key, int) for key in names_raw.keys()):
            return None, "names 字典的键必须是 int 类型"
        if not all(isinstance(name, str) and name for name in names_raw.values()):
            return None, "names 字典的值必须是字符串类型"
        return len(names_raw), ""

    return None, f"names 不是合法的列表或字典: {type(names_raw).__name__}"
