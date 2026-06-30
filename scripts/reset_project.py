import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLATFORM_SRC = REPO_ROOT / "apps" / "platform" / "src"

if str(PLATFORM_SRC) not in sys.path:
    sys.path.insert(0, str(PLATFORM_SRC))

from od_platform.cli.reset_project import reset_project


def main() -> None:
    raise SystemExit(reset_project())


if __name__ == "__main__":
    main()
