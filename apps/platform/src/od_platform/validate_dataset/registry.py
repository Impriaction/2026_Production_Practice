#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :registry.py
# @Time      :2026/7/2 09:21:32
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :data_validation注册表+数据契约(CheckResult + CheckSeverity + CheckContext)

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List

from od_platform.common.registry_utils import import_submodules

logger = logging.getLogger(__name__)


# 1. CheckSeverity - 严重程度
class CheckSeverity:
    INFO = "INFO"  # 告知级别: 工程上知道一下, 不阻断
    WARNING = "WARNING"  # 关注级别: 能继续, 但需要人工 review
    ERROR = "ERROR"  # 阻塞级别 CI必须听, 训练绝对不能继续
    PASS = "PASS"  # 通过

    _ORDER = {INFO: 1, WARNING: 2, ERROR: 3, PASS: 0}

    @classmethod
    def rank(cls, level: str) -> int:
        return cls._ORDER.get(level, 0)


# 2. CheckResult - 单个 check 的统一返回类型
@dataclass
class CheckResult:
    name: str
    severity: str
    summary: str  # 一句话总结, 供终端日志 / 报告的头部使用, 给人看的
    details: Dict[str, Any] = field(default_factory=dict)  # 结构化详情字典 - json报告给机器看的

    @property
    def passed(self) -> bool:
        return self.severity in (CheckSeverity.PASS, CheckSeverity.INFO)


# 3. CheckContext - check函数的入参
@dataclass
class CheckContext:
    """check函数的入参: 所有check函数的签名都是这一个"""

    yaml_path: Path


CheckFunc = Callable[[CheckContext], CheckResult]


# 4. 注册表条目
@dataclass(frozen=True)
class CheckEntry:
    """注册表中的一条记录。forzen=注册后不可改"""

    name: str
    func: CheckFunc

    @property
    def check(self) -> CheckFunc:
        return self.func


# 模块级别的注册表
_REGISTRY: Dict[str, CheckEntry] = {}


def check(name: str) -> Callable[[CheckFunc], CheckFunc]:
    def decorator(func: CheckFunc) -> CheckFunc:
        if name in _REGISTRY:
            raise ValueError(
                f"check {name} 重复注册-第二次出现在 {func.__module__}.{func.__name__}"
            )
        _REGISTRY[name] = CheckEntry(name=name, func=func)
        return func

    return decorator


# 兼容之前的命名
register_check = check


# 自动import - 加新的check不改框架代码的物理基础
_LAZY_INITIALIZED = False


def _lazy_init() -> None:
    """扫描 checks/*.py 自动触发 @register。

    - 跳过 _ 开头的私有模块。
    - 标志位放在 import 全部成功【之后】, 任何 import 失败都不污染状态, 下次可重试。
    """

    global _LAZY_INITIALIZED
    if _LAZY_INITIALIZED:
        return

    from od_platform.validate_dataset import checks

    import_submodules(checks)
    _LAZY_INITIALIZED = True


# 定义查询的API
def get_all_checks() -> List[CheckEntry]:
    """返回全部注册的check"""

    _lazy_init()
    return list(_REGISTRY.values())


def get_check(name: str) -> CheckEntry:
    _lazy_init()
    if name not in _REGISTRY:
        raise ValueError(f"check {name} 未注册-已经注册的检查有: {list(_REGISTRY)}")
    return _REGISTRY[name]


def list_check_names() -> List[str]:
    """返回已经注册的名字列表"""

    _lazy_init()
    return list(_REGISTRY.keys())


# 兼容之前的命名
def list_checks() -> List[str]:
    return list_check_names()


def run_checks(
    context: CheckContext,
    *,
    selected: List[str] | None = None,
) -> List[CheckResult]:
    _lazy_init()
    names = selected if selected is not None else list_check_names()
    return [get_check(name).func(context) for name in names]


def worst_severity(results: List[CheckResult]) -> str:
    if not results:
        return CheckSeverity.PASS
    return max(results, key=lambda item: CheckSeverity.rank(item.severity)).severity
