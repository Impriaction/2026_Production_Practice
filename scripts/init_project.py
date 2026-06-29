import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLATFORM_SRC = REPO_ROOT / "apps" / "platform" / "src"

if str(PLATFORM_SRC) not in sys.path:
    sys.path.insert(0, str(PLATFORM_SRC))

from od_platform.cli.init_project import initialize_project
from od_platform.common.logging_utils import log_execution_time

logger = logging.getLogger("od_platform")


def main() -> None:
    initialize_project()

if __name__ == "__main__":
    main()
