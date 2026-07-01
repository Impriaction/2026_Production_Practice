#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : strategy_registry.py
# @Author    : ODPlatform team
# @Project   : ODPlatform
# @Function  : Split strategy registry + shared option bag

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from od_platform.common.constants import DEFAULT_RANDOM_STATE
from od_platform.common.registry_utils import import_submodules

from .manifest import PairList, SplitManifest

logger = logging.getLogger(__name__)


@dataclass
class SplitOptions:
    """Shared parameter bag for all split strategies."""

    train_rate: float | int = 0.8
    val_rate: float | int = 0.1
    random_state: int = DEFAULT_RANDOM_STATE
    labels_per_image: Optional[Dict[str, List[str]]] = field(default=None)
    group_per_image: Optional[Dict[str, str]] = field(default=None)


SplitStrategyFunc = Callable[[PairList, SplitOptions], SplitManifest]


@dataclass(frozen=True)
class StrategyEntry:
    """One registry entry: strategy function + capability metadata."""

    func: SplitStrategyFunc
    requires_labels: bool = False


_STRATEGY_REGISTRY: Dict[str, StrategyEntry] = {}
_LAZY_INITIALIZED = False


def register_strategy(
    name: str,
    *,
    requires_labels: bool = False,
) -> Callable[[SplitStrategyFunc], SplitStrategyFunc]:
    """Register one split strategy into the strategy registry."""

    def decorator(func: SplitStrategyFunc) -> SplitStrategyFunc:
        if name in _STRATEGY_REGISTRY:
            logger.warning("Strategy %s already registered, later one will override it.", name)
        _STRATEGY_REGISTRY[name] = StrategyEntry(
            func=func,
            requires_labels=requires_labels,
        )
        logger.debug("Registered split strategy: %s", name)
        return func

    return decorator


def get_strategy(name: str) -> StrategyEntry:
    """Get one strategy entry by name."""

    _lazy_init()
    if name not in _STRATEGY_REGISTRY:
        raise ValueError(f"Unregistered split strategy: {name!r}. Available: {sorted(_STRATEGY_REGISTRY)}")
    return _STRATEGY_REGISTRY[name]


def list_strategies() -> Tuple[str, ...]:
    """Return all registered split strategy names."""

    _lazy_init()
    return tuple(sorted(_STRATEGY_REGISTRY))


def _lazy_init() -> None:
    """Import strategies package once so decorators can register strategies."""

    global _LAZY_INITIALIZED
    if _LAZY_INITIALIZED:
        return

    from . import strategies

    import_submodules(strategies)
    _LAZY_INITIALIZED = True
