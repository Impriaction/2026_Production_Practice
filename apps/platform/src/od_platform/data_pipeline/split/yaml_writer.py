#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : yaml_writer.py
# @Author    : ODPlatform team
# @Project   : ODPlatform
# @Function  : YAML writing helpers for split outputs

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from .materializer import SplitOutputDirs


def build_dataset_yaml_doc(
    dataset_root: Path,
    dirs: SplitOutputDirs,
    class_names: Sequence[str],
) -> dict[str, object]:
    """Build a YOLO-style dataset yaml document from SplitOutputDirs."""

    rel_dirs = dirs.relative_image_dirs(dataset_root)
    names = list(class_names)
    return {
        "path": str(dataset_root),
        "train": rel_dirs["train"],
        "val": rel_dirs["val"],
        "test": rel_dirs["test"],
        "nc": len(names),
        "names": names,
    }


def dump_dataset_yaml_lines(doc: dict[str, object]) -> list[str]:
    """Serialize a simple dataset yaml document without external deps."""

    lines = [
        f'path: "{doc["path"]}"',
        f'train: "{doc["train"]}"',
        f'val: "{doc["val"]}"',
        f'test: "{doc["test"]}"',
        f'nc: {doc["nc"]}',
        "names:",
    ]
    for index, name in enumerate(doc["names"]):
        lines.append(f"  {index}: {name}")
    return lines


def write_dataset_yaml(
    yaml_path: Path,
    *,
    dataset_root: Path,
    classes: Sequence[str],
    manifest: Any | None = None,
    dataset_name: str | None = None,
    source_format: str | None = None,
    task: str | None = None,
    dirs: SplitOutputDirs | None = None,
) -> dict[str, object]:
    """Write the dataset yaml file and return the doc object."""

    if dirs is None:
        dirs = SplitOutputDirs.for_dataset_root(dataset_root)

    doc = build_dataset_yaml_doc(dataset_root, dirs, classes)
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text("\n".join(dump_dataset_yaml_lines(doc)) + "\n", encoding="utf-8")
    return doc
