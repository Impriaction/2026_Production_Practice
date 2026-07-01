#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : materializer.py
# @Author    : ODPlatform team
# @Project   : ODPlatform
# @Function  : Materialize SplitManifest into train/val/test directories

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .manifest import PairList, SplitManifest

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SplitOutputDirs:
    train_images: Path
    val_images: Path
    test_images: Path
    train_labels: Path
    val_labels: Path
    test_labels: Path

    @classmethod
    def for_dataset_root(cls, root: Path) -> "SplitOutputDirs":
        return cls(
            train_images=root / "train" / "images",
            val_images=root / "val" / "images",
            test_images=root / "test" / "images",
            train_labels=root / "train" / "labels",
            val_labels=root / "val" / "labels",
            test_labels=root / "test" / "labels",
        )

    def all_dirs(self) -> tuple[Path, ...]:
        return (
            self.train_images,
            self.train_labels,
            self.val_images,
            self.val_labels,
            self.test_images,
            self.test_labels,
        )

    def relative_image_dirs(self, dataset_root: Path) -> Dict[str, str]:
        """Expose train/val/test image dirs relative to dataset_root."""

        root = dataset_root.resolve()
        return {
            "train": self.train_images.resolve().relative_to(root).as_posix(),
            "val": self.val_images.resolve().relative_to(root).as_posix(),
            "test": self.test_images.resolve().relative_to(root).as_posix(),
        }


def _place(src: Path, dst: Path) -> None:
    if dst.exists():
        dst.unlink()

    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _materialize_one(pairs: PairList, images_dir: Path, labels_dir: Path) -> int:
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    for img, lbl in pairs:
        _place(img, images_dir / img.name)
        _place(lbl, labels_dir / lbl.name)

    return len(pairs)


def materialize(manifest: SplitManifest, dirs: SplitOutputDirs) -> Dict[str, int]:
    for directory in dirs.all_dirs():
        if directory.exists():
            shutil.rmtree(directory)

    counts = {
        "train": _materialize_one(manifest.train, dirs.train_images, dirs.train_labels),
        "val": _materialize_one(manifest.val, dirs.val_images, dirs.val_labels),
        "test": _materialize_one(manifest.test, dirs.test_images, dirs.test_labels),
    }

    logger.info("materialized %s samples to %s", counts, dirs)
    return counts
