from __future__ import annotations

import random
from typing import Sequence, Tuple, TypeVar

from od_platform.common.constants import RATE_EPSILON

T = TypeVar("T")


def validate_rates(train_rate: float | int, val_rate: float | int) -> float:
    """Validate split ratios and return inferred test_rate."""

    train = float(train_rate)
    val = float(val_rate)
    test_rate = 1.0 - train - val
    if not (0 <= train <= 1 and 0 <= val <= 1 and -RATE_EPSILON <= test_rate <= 1):
        raise ValueError(f"比例越界: train={train_rate}, val={val_rate}, test={test_rate}")
    return max(0.0, test_rate)


def three_way_counts(n: int, train_rate: float | int, val_rate: float | int) -> Tuple[int, int, int]:
    """Convert split ratios into clamped train/val/test counts."""

    n_train = int(round(n * float(train_rate)))
    n_val = int(round(n * float(val_rate)))
    n_train = max(0, min(n_train, n))
    n_val = max(0, min(n_val, n - n_train))
    return n_train, n_val, n - n_train - n_val


def seeded_shuffled(seq: Sequence[T], rng: random.Random) -> list[T]:
    """Return a shuffled copy using the provided RNG."""

    out = list(seq)
    rng.shuffle(out)
    return out
