#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : manifest.py
# @Author    : ODPlatform team
# @Project   : ODPlatform
# @Function  : Compose split results into one manifest object

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


Pair = Tuple[Path, Path]
PairList = List[Pair]


@dataclass
class SplitManifest:
    """One split result object: three sample groups + reproducible metadata."""

    train: PairList = field(default_factory=list)
    val: PairList = field(default_factory=list)
    test: PairList = field(default_factory=list)

    train_rate: float | int = 0.8
    val_rate: float | int = 0.1
    test_rate: float | int = 0.1
    random_state: int = 1210
    strategy: str = "random"

    def summary(self) -> Dict[str, int]:
        return {
            "train": len(self.train),
            "val": len(self.val),
            "test": len(self.test),
            "total": len(self.train) + len(self.val) + len(self.test),
        }
