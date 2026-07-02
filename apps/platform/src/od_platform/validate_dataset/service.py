#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :service.py
# @Time      :2026/7/2 10:15:37
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :validate_dataset 调度层 要跑所有的检查

from __future__ import annotations

import logging
from typing import List

from od_platform.common.performance_utils import time_it
from od_platform.validate_dataset.registry import (
    CheckContext,
    CheckEntry,
    CheckResult,
    CheckSeverity,
    get_all_checks,
)

logger = logging.getLogger(__name__)


@time_it(name="所有检测耗时总计", logger_instance=logger, iterations=1)
def run_all_checks(ctx: CheckContext) -> List[CheckResult]:
    """跑全部注册的check，收集结果"""

    entries = get_all_checks()
    logger.info(f"开始执行 {len(entries)} 个 checks")
    results: List[CheckResult] = []

    for entry in entries:
        result = _safe_run_one(entry, ctx)
        _log_check_result(result)
        results.append(result)

    _log_summary(results)
    return results


@time_it(
    name=lambda entry, ctx: f"检查: [{entry.name}]",
    logger_instance=logger,
    iterations=1,
)
def _safe_run_one(entry: CheckEntry, ctx: CheckContext) -> CheckResult:
    """跑单个check，异常做好包装"""

    try:
        return entry.func(ctx)
    except Exception as e:
        logger.exception(f"check {entry.name} 出现异常，已捕获走 ERROR 级结果")
        return CheckResult(
            name=entry.name,
            severity=CheckSeverity.ERROR,
            summary=f"check {entry.name} 出现异常，{type(e).__name__}: {e}",
            details={
                "exception_type": type(e).__name__,
                "exception_msg": str(e),
            },
        )


def _log_check_result(r: CheckResult) -> None:
    log_method = {
        CheckSeverity.ERROR: logger.error,
        CheckSeverity.WARNING: logger.warning,
        CheckSeverity.INFO: logger.info,
        CheckSeverity.PASS: logger.debug,
    }.get(r.severity, logger.info)

    log_method(f"[{r.severity:7s}] {r.name}: {r.summary}")


def _log_summary(results: List[CheckResult]) -> None:
    counts = {}
    for r in results:
        counts[r.severity] = counts.get(r.severity, 0) + 1

    parts = [f"{n} {s}" for s, n in counts.items()]
    logger.info(f"检查完成，结果如下: {' / '.join(parts)}")
