from pathlib import Path
from typing import Iterable, List, Optional, Tuple

WORKSPACE_MARKER = ".odp-workspace"


def _find_workspace_root(
    start: Path,
    markers: Tuple[str, ...] = (WORKSPACE_MARKER,),
) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent

    for parent in [current, *current.parents]:
        for marker in markers:
            if (parent / marker).exists():
                return parent

    raise FileNotFoundError(
        f"Cannot find workspace marker {markers}. "
        f"Make sure {WORKSPACE_MARKER} exists in the repository root."
    )


ROOT_DIR: Path = _find_workspace_root(Path(__file__))
APP_DIR: Path = ROOT_DIR / "apps" / "platform"

DATA_DIR: Path = ROOT_DIR / "data"
MODELS_DIR: Path = ROOT_DIR / "models"
RUNS_DIR: Path = ROOT_DIR / "runs"

PRETRAINED_MODELS_DIR: Path = MODELS_DIR / "pretrained"
TRAINED_MODELS_DIR: Path = MODELS_DIR / "trained"

RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"

CONFIGS_DIR: Path = APP_DIR / "configs"
LOGGING_DIR: Path = APP_DIR / "logging"
META_LOGGING_DIR: Path = APP_DIR / "meta_logging"
UNIT_TEST_DIR: Path = APP_DIR / "tests"

DOCS_DIR: Path = ROOT_DIR / "docs"
SCRIPTS_DIR: Path = ROOT_DIR / "scripts"
SRC_DIR: Path = APP_DIR / "src"
RESET_BACKUPS_DIR: Path = META_LOGGING_DIR / "reset_backups"
RESET_AUDIT_DIR: Path = META_LOGGING_DIR / "reset_audit"

PROTECTED_RESET_PATHS: Tuple[Path, ...] = (
    ROOT_DIR,
    ROOT_DIR / ".git",
    ROOT_DIR / WORKSPACE_MARKER,
    SRC_DIR,
    CONFIGS_DIR,
    DOCS_DIR,
    SCRIPTS_DIR,
    PRETRAINED_MODELS_DIR,
    META_LOGGING_DIR,
)

RESET_SCOPE_DIRS = {
    "runtime": (
        RUNS_DIR,
        TRAINED_MODELS_DIR,
        PROCESSED_DATA_DIR,
        LOGGING_DIR,
    ),
    "runtime-plus-raw": (
        RUNS_DIR,
        TRAINED_MODELS_DIR,
        PROCESSED_DATA_DIR,
        LOGGING_DIR,
        RAW_DATA_DIR,
    ),
    "full": (
        RUNS_DIR,
        TRAINED_MODELS_DIR,
        PROCESSED_DATA_DIR,
        LOGGING_DIR,
        RAW_DATA_DIR,
        DATA_DIR,
        MODELS_DIR,
    ),
}


def get_dirs_to_initialize() -> List[Path]:
    return [
        DATA_DIR,
        MODELS_DIR,
        RUNS_DIR,
        PRETRAINED_MODELS_DIR,
        TRAINED_MODELS_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        CONFIGS_DIR,
        LOGGING_DIR,
        META_LOGGING_DIR,
        UNIT_TEST_DIR,
        DOCS_DIR,
        SCRIPTS_DIR,
    ]


def get_protected_reset_paths() -> Tuple[Path, ...]:
    return PROTECTED_RESET_PATHS


def get_dirs_to_reset(scope: str = "runtime") -> List[Path]:
    try:
        return list(RESET_SCOPE_DIRS[scope])
    except KeyError as exc:
        raise ValueError(f"Unsupported reset scope: {scope}") from exc


def is_protected_reset_path(path: Path, protected_paths: Optional[Iterable[Path]] = None) -> bool:
    resolved = path.resolve()
    candidates = protected_paths if protected_paths is not None else PROTECTED_RESET_PATHS
    root_resolved = ROOT_DIR.resolve()
    for protected in candidates:
        protected_resolved = protected.resolve()
        if resolved == protected_resolved:
            return True
        if protected_resolved != root_resolved and protected_resolved in resolved.parents:
            return True
    return False
