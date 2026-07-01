#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : refs.py
# @Author    : ODPlatform team
# @Project   : ODPlatform
# @Function  : Reference resolution helpers

"""
引用解析: 把命令行用户给的 dataset / yaml / model / 资源名或路径统一解析成 Path。

Examples:
    --dataset rsod
    --dataset /path/to/rsod
    --model resnet50
    --model /path/to/resnet50
    --config config.yaml
    --config /path/to/config.yaml
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from od_platform.common.paths import CONFIGS_DIR, PRETRAINED_MODELS_DIR, RAW_DATA_DIR


def resolve_ref(ref: str, *, base_dir: Path, default_suffix: Optional[str] = None) -> Path:
    p = Path(ref)
    if p.is_absolute():
        return p.resolve()

    if default_suffix and p.suffix == "":
        p = p.with_suffix(default_suffix)
    return (base_dir / p).resolve()


def resolve_dataset(ref: str) -> Path:
    return resolve_ref(ref, base_dir=RAW_DATA_DIR)


def resolve_model(ref: str) -> Path:
    return resolve_ref(ref, base_dir=PRETRAINED_MODELS_DIR)


def resolve_config(ref: str) -> Path:
    return resolve_ref(ref, base_dir=CONFIGS_DIR, default_suffix=".yaml")


def resolve_resource(ref: str, *, base_dir: Path, default_suffix: Optional[str] = None) -> Path:
    return resolve_ref(ref, base_dir=base_dir, default_suffix=default_suffix)
