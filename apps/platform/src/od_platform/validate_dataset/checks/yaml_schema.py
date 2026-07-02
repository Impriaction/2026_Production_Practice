#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :yaml_schema.py
# @Time      :2026/7/2 13:01:52
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :yaml schema validation

from __future__ import annotations

from typing import Any

from od_platform.validate_dataset.checks._shared import load_yaml_doc_or_error
from od_platform.validate_dataset.registry import CheckContext, CheckResult, CheckSeverity, check


@check("yaml_schema", order=10)
def validate_yaml_schema(ctx: CheckContext) -> CheckResult:
    cfg, error = load_yaml_doc_or_error(ctx, "yaml_schema")
    if error is not None:
        return error

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
        problems.append(f"nc 字段的值({nc})与 names 字段中元素个数({names_count})不相等")

    for field_name in ("path", "train", "val", "test"):
        value = cfg.get(field_name)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{field_name} 字段不存在或者不是非空字符串: {value}")

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
