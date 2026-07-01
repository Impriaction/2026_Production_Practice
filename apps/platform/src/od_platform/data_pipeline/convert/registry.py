from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from od_platform.common.registry_utils import import_submodules

logger = logging.getLogger(__name__)


@dataclass
class ConvertOptions:
    """
    Shared parameter bag for all converters.

    task:
        Target task, such as detect / segment.
    classes:
        Class whitelist and class-id order.
        - None: auto-discover classes while converting.
        - [...]: keep only listed classes and use that order as class_id.
    """

    task: str = "detect"
    classes: Optional[List[str]] = field(default=None)


ConverterFunc = Callable[[Path, Path, ConvertOptions], List[str]]


@dataclass(frozen=True)
class ConverterEntry:
    """One registry entry: implementation function + supported tasks."""

    func: ConverterFunc
    supported_tasks: Tuple[str, ...]

    def supports(self, task: str) -> bool:
        return task in self.supported_tasks


_REGISTRY: Dict[str, ConverterEntry] = {}
_LAZY_INITIALIZED = False


def register(
    format_name: str,
    *,
    supported_tasks: Tuple[str, ...],
) -> Callable[[ConverterFunc], ConverterFunc]:
    """Decorator that registers one converter into the registry."""

    def decorator(func: ConverterFunc) -> ConverterFunc:
        if format_name in _REGISTRY:
            logger.warning("Format %s is registered twice; later one overrides previous one.", format_name)
        _REGISTRY[format_name] = ConverterEntry(
            func=func,
            supported_tasks=tuple(supported_tasks),
        )
        logger.debug("Registered converter: format=%s, tasks=%s", format_name, supported_tasks)
        return func

    return decorator


def get_converter(format_name: str) -> ConverterEntry:
    """Get a converter entry by format name."""

    _lazy_init()
    if format_name not in _REGISTRY:
        raise ValueError(f"Unregistered format: {format_name!r}. Available: {sorted(_REGISTRY)}")
    return _REGISTRY[format_name]


def available_formats() -> List[str]:
    """Return all registered format names."""

    _lazy_init()
    return sorted(_REGISTRY)


def list_capabilities() -> Dict[str, Tuple[str, ...]]:
    """Return all registered formats and their supported tasks."""

    _lazy_init()
    return {fmt: entry.supported_tasks for fmt, entry in _REGISTRY.items()}


def _lazy_init() -> None:
    """
    Scan converters/ and import each non-private module once so that
    @register decorators run automatically.
    """

    global _LAZY_INITIALIZED
    if _LAZY_INITIALIZED:
        return

    from . import converters

    import_submodules(converters)
    _LAZY_INITIALIZED = True
