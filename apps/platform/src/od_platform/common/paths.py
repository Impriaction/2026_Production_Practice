from pathlib import Path
from typing import List, Tuple

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
UNIT_TEST_DIR: Path = APP_DIR / "tests"

DOCS_DIR: Path = ROOT_DIR / "docs"
SCRIPTS_DIR: Path = ROOT_DIR / "scripts"


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
        UNIT_TEST_DIR,
        DOCS_DIR,
        SCRIPTS_DIR,
    ]
