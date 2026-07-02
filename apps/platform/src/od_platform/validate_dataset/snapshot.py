#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :snapshot.py
# @Time      :2026/7/2 14:45:37
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :dataset snapshot - 一次扫描多次复用

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

from od_platform.common.constants import IMAGE_EXTENSIONS, Task
from od_platform.common.performance_utils import time_it

logger = logging.getLogger(__name__)
SPLIT_ORDER: tuple[str, ...] = ("train", "val", "test")
IMAGE_EXTENSION_SET = {suffix.lower() for suffix in IMAGE_EXTENSIONS}


@dataclass(frozen=True)
class SplitStats:
    image_count: int
    annotated_count: int
    total_instances: int


@dataclass(frozen=True)
class SplitFiles:
    split: str
    images_dir: Path
    labels_dir: Path
    images_dir_exists: bool
    labels_dir_exists: bool
    image_paths: Tuple[Path, ...]
    label_paths: Tuple[Path, ...]
    image_by_stem: Dict[str, Path]
    label_by_stem: Dict[str, Path]
    image_stems: frozenset[str]
    label_stems: frozenset[str]
    pairs: Tuple[tuple[Path, Path], ...]


@dataclass(frozen=True)
class DatasetSnapshot:
    """对数据集做一次完整快照，供所有 check 共享消费。"""

    yaml_path: Path
    yaml_data: Dict[str, Any]
    yaml_load_error: Optional[str]
    data_root: Path
    nc: Optional[int]
    class_names: Tuple[str, ...]
    task_type: str
    images_per_split: Dict[str, Tuple[Path, ...]]
    labels_per_split: Dict[str, Tuple[Path, ...]]
    stats_per_split: Dict[str, SplitStats]
    split_files: Dict[str, SplitFiles] = field(default_factory=dict)
    scan_warnings: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def splits(self) -> Tuple[str, ...]:
        return tuple(split for split in SPLIT_ORDER if split in self.images_per_split)

    @property
    def total_images(self) -> int:
        return sum(len(images) for images in self.images_per_split.values())


def _load_yaml(yaml_path: Path) -> Tuple[Dict[str, Any], Optional[str]]:
    if not yaml_path.exists():
        return {}, f"YAML file does not exist: {yaml_path}"

    try:
        with yaml_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        if not isinstance(data, dict):
            return {}, f"YAML 的顶层不是一个 dict: {type(data).__name__}"
        return data, None
    except yaml.YAMLError as exc:
        return {}, f"Error loading YAML file: {exc}"
    except OSError as exc:
        return {}, f"Error reading YAML file: {exc}"


def _resolve_data_root(yaml_path: Path, yaml_data: Dict[str, Any]) -> Path:
    raw = yaml_data.get("path")
    if not isinstance(raw, str) or not raw.strip():
        return yaml_path.parent.resolve()

    root = Path(raw)
    if root.is_absolute():
        return root.resolve()
    return (yaml_path.parent / root).resolve()


def _normalize_class_names(yaml_data: Dict[str, Any]) -> Tuple[Tuple[str, ...], Optional[int]]:
    names = yaml_data.get("names")
    nc = yaml_data.get("nc")
    nc_value = nc if isinstance(nc, int) and nc > 0 else None

    if isinstance(names, list):
        normalized = tuple(name for name in names if isinstance(name, str) and name)
        return normalized, nc_value

    if isinstance(names, dict):
        ordered: list[str] = []
        for key in sorted(names):
            value = names[key]
            if isinstance(key, int) and isinstance(value, str) and value:
                ordered.append(value)
        return tuple(ordered), nc_value

    return tuple(), nc_value


def _resolve_split_image_dir(data_root: Path, yaml_data: Dict[str, Any], split: str) -> Optional[Path]:
    raw = yaml_data.get(split)
    if not isinstance(raw, str) or not raw.strip():
        return None

    path = Path(raw)
    if path.is_absolute():
        return path.resolve()
    return (data_root / path).resolve()


def _count_instances(label_paths: Tuple[Path, ...]) -> int:
    total = 0
    for label_path in label_paths:
        for raw_line in label_path.read_text(encoding="utf-8").splitlines():
            if raw_line.strip():
                total += 1
    return total


def _scan_split(split: str, images_dir: Path) -> tuple[SplitFiles, SplitStats]:
    labels_dir = images_dir.parent / "labels"

    image_paths: Tuple[Path, ...] = tuple()
    if images_dir.is_dir():
        image_paths = tuple(
            sorted(
                path
                for path in images_dir.iterdir()
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSION_SET
            )
        )

    label_paths: Tuple[Path, ...] = tuple()
    if labels_dir.is_dir():
        label_paths = tuple(sorted(path for path in labels_dir.glob("*.txt") if path.is_file()))

    image_by_stem = {path.stem: path for path in image_paths}
    label_by_stem = {path.stem: path for path in label_paths}
    common_stems = sorted(image_by_stem.keys() & label_by_stem.keys())
    pairs = tuple((image_by_stem[stem], label_by_stem[stem]) for stem in common_stems)

    split_files = SplitFiles(
        split=split,
        images_dir=images_dir,
        labels_dir=labels_dir,
        images_dir_exists=images_dir.is_dir(),
        labels_dir_exists=labels_dir.is_dir(),
        image_paths=image_paths,
        label_paths=label_paths,
        image_by_stem=image_by_stem,
        label_by_stem=label_by_stem,
        image_stems=frozenset(image_by_stem),
        label_stems=frozenset(label_by_stem),
        pairs=pairs,
    )
    split_stats = SplitStats(
        image_count=len(image_paths),
        annotated_count=len(label_paths),
        total_instances=_count_instances(label_paths),
    )
    return split_files, split_stats


@time_it(name="build_dataset_snapshot", logger_instance=logger, iterations=1)
def build_dataset_snapshot(
    yaml_path: Path,
    *,
    yaml_data: Optional[Dict[str, Any]] = None,
    task_type: str = Task.DETECT,
) -> DatasetSnapshot:
    loaded_yaml, yaml_load_error = (yaml_data, None) if yaml_data is not None else _load_yaml(yaml_path)
    yaml_payload = loaded_yaml or {}
    data_root = _resolve_data_root(yaml_path, yaml_payload)
    class_names, nc = _normalize_class_names(yaml_payload)

    images_per_split: Dict[str, Tuple[Path, ...]] = {}
    labels_per_split: Dict[str, Tuple[Path, ...]] = {}
    stats_per_split: Dict[str, SplitStats] = {}
    split_files_map: Dict[str, SplitFiles] = {}
    scan_warnings: list[str] = []

    if yaml_load_error is None:
        for split in SPLIT_ORDER:
            images_dir = _resolve_split_image_dir(data_root, yaml_payload, split)
            if images_dir is None:
                continue

            split_files, split_stats = _scan_split(split, images_dir)
            split_files_map[split] = split_files
            images_per_split[split] = split_files.image_paths
            labels_per_split[split] = split_files.label_paths
            stats_per_split[split] = split_stats

            if not split_files.images_dir_exists:
                scan_warnings.append(f"{split} images dir missing: {split_files.images_dir}")
            if not split_files.labels_dir_exists:
                scan_warnings.append(f"{split} labels dir missing: {split_files.labels_dir}")

    return DatasetSnapshot(
        yaml_path=yaml_path,
        yaml_data=yaml_payload,
        yaml_load_error=yaml_load_error,
        data_root=data_root,
        nc=nc,
        class_names=class_names,
        task_type=task_type,
        images_per_split=images_per_split,
        labels_per_split=labels_per_split,
        stats_per_split=stats_per_split,
        split_files=split_files_map,
        scan_warnings=tuple(scan_warnings),
    )
