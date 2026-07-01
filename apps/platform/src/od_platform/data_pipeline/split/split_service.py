from __future__ import annotations

import logging
from typing import Dict, List, Optional

from od_platform.common.constants import DEFAULT_RANDOM_STATE, DEFAULT_SPLIT_STRATEGY

from .manifest import PairList, SplitManifest
from .strategy_registry import SplitOptions, get_strategy

logger = logging.getLogger(__name__)


def split_pairs(
    pairs: PairList,
    train_rate: float | int = 0.8,
    val_rate: float | int = 0.1,
    random_state: int = DEFAULT_RANDOM_STATE,
    *,
    strategy: str = DEFAULT_SPLIT_STRATEGY,
    labels_per_image: Optional[Dict[str, List[str]]] = None,
    group_per_image: Optional[Dict[str, str]] = None,
) -> SplitManifest:
    """
    Split image/label pairs by the named strategy and return one SplitManifest.

    labels_per_image:
        Optional label metadata required by some future advanced strategies.
    group_per_image:
        Optional grouping metadata for grouped split strategies.
    """

    entry = get_strategy(strategy)
    if entry.requires_labels and labels_per_image is None:
        raise ValueError(f"划分策略 {strategy!r} 需要 labels_per_image，但当前未提供。")

    options = SplitOptions(
        train_rate=train_rate,
        val_rate=val_rate,
        random_state=random_state,
        labels_per_image=labels_per_image,
        group_per_image=group_per_image,
    )
    manifest = entry.func(pairs, options)
    logger.info("Split %s pairs with strategy=%s -> %s", len(pairs), strategy, manifest.summary())
    return manifest
