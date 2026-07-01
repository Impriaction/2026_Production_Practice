from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType


def import_submodules(package: ModuleType) -> None:
    """
    Import all non-private submodules under a package to trigger decorators
    such as @register and finish auto-registration.
    """
    for module_info in pkgutil.iter_modules(package.__path__):
        if not module_info.name.startswith("_"):
            importlib.import_module(f"{package.__name__}.{module_info.name}")
