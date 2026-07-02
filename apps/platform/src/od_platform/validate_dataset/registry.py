#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :registry.py
# @Time      :2026/7/2 09:21:32
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :data_validation 注册表与共享上下文

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List

import yaml

from od_platform.common.registry_utils import import_submodules
from od_platform.validate_dataset.snapshot import DatasetSnapshot, build_dataset_snapshot

logger = logging.getLogger(__name__)
SPLIT_NAMES: tuple[str, ...] = ("train", "val", "test")


class CheckSeverity:
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    PASS = "PASS"

    _ORDER = {INFO: 1, WARNING: 2, ERROR: 3, PASS: 0}

    @classmethod
    def rank(cls, level: str) -> int:
        return cls._ORDER.get(level, 0)


@dataclass
class CheckResult:
    name: str
    severity: str
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.severity in (CheckSeverity.PASS, CheckSeverity.INFO)


@dataclass
class CheckContext:
    """Shared validation context with lazy yaml parsing and split scanning."""

    yaml_path: Path
    _yaml_doc_cache: Dict[str, Any] | None = field(default=None, init=False, repr=False)
    _dataset_root_cache: Path | None = field(default=None, init=False, repr=False)
    _split_dirs_cache: Dict[str, Path] | None = field(default=None, init=False, repr=False)
    _snapshot_cache: DatasetSnapshot | None = field(default=None, init=False, repr=False)

    @property
    def yaml_loaded(self) -> bool:
        return self._yaml_doc_cache is not None

    @property
    def snapshot_loaded(self) -> bool:
        return self._snapshot_cache is not None

    @property
    def yaml_doc(self) -> Dict[str, Any]:
        if self._yaml_doc_cache is None:
            with self.yaml_path.open("r", encoding="utf-8") as file:
                doc = yaml.safe_load(file)
            if not isinstance(doc, dict):
                raise ValueError(f"yaml top-level must be dict, got {type(doc).__name__}")
            self._yaml_doc_cache = doc
        return self._yaml_doc_cache

    @property
    def dataset_root(self) -> Path:
        if self._dataset_root_cache is None:
            path_value = self.yaml_doc.get("path")
            if not isinstance(path_value, str) or not path_value.strip():
                raise ValueError("yaml field 'path' must be a non-empty string")
            self._dataset_root_cache = self._resolve_path(path_value, self.yaml_path.parent)
        return self._dataset_root_cache

    @property
    def split_image_dirs(self) -> Dict[str, Path]:
        if self._split_dirs_cache is None:
            split_dirs: Dict[str, Path] = {}
            for split in SPLIT_NAMES:
                raw_value = self.yaml_doc.get(split)
                if not isinstance(raw_value, str) or not raw_value.strip():
                    raise ValueError(f"yaml field '{split}' must be a non-empty string")
                split_dirs[split] = self._resolve_path(raw_value, self.dataset_root)
            self._split_dirs_cache = split_dirs
        return self._split_dirs_cache

    @property
    def split_snapshot(self) -> DatasetSnapshot:
        if self._snapshot_cache is None:
            self._snapshot_cache = build_dataset_snapshot(
                self.yaml_path,
                yaml_data=self._yaml_doc_cache,
            )
        return self._snapshot_cache

    def _resolve_path(self, raw_path: str, base_dir: Path) -> Path:
        path = Path(raw_path)
        if path.is_absolute():
            return path.resolve()
        return (base_dir / path).resolve()
CheckFunc = Callable[[CheckContext], CheckResult]


@dataclass(frozen=True)
class CheckEntry:
    name: str
    func: CheckFunc
    order: int = 100

    @property
    def check(self) -> CheckFunc:
        return self.func


_REGISTRY: Dict[str, CheckEntry] = {}


def check(name: str, *, order: int = 100) -> Callable[[CheckFunc], CheckFunc]:
    def decorator(func: CheckFunc) -> CheckFunc:
        if name in _REGISTRY:
            raise ValueError(
                f"check {name} 重复注册-第二次出现在 {func.__module__}.{func.__name__}"
            )
        _REGISTRY[name] = CheckEntry(name=name, func=func, order=order)
        return func

    return decorator


register_check = check
_LAZY_INITIALIZED = False


def _lazy_init() -> None:
    """Import checks package once and trigger decorators."""

    global _LAZY_INITIALIZED
    if _LAZY_INITIALIZED:
        return

    from od_platform.validate_dataset import checks

    import_submodules(checks)
    _LAZY_INITIALIZED = True


def get_all_checks() -> List[CheckEntry]:
    _lazy_init()
    return sorted(_REGISTRY.values(), key=lambda entry: (entry.order, entry.name))


def get_check(name: str) -> CheckEntry:
    _lazy_init()
    if name not in _REGISTRY:
        raise ValueError(f"check {name} 未注册-已经注册的检查有: {list(_REGISTRY)}")
    return _REGISTRY[name]


def list_check_names() -> List[str]:
    _lazy_init()
    return [entry.name for entry in get_all_checks()]


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
