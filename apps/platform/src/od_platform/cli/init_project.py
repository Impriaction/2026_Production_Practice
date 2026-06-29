import logging
import sys
from pathlib import Path
from typing import List

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from od_platform.common.logging_utils import get_logger, log_execution_time
from od_platform.common.paths import LOGGING_DIR, ROOT_DIR, get_dirs_to_initialize
from od_platform.common.string_utils import format_table_row, format_table_separator

LINE_WIDTH = 60
TABLE_WIDTHS = [30, 12]
TABLE_ALIGNS = ["left", "right"]

logger = logging.getLogger("od_platform.cli.init_project")


@log_execution_time(logger_name="od_platform", message="init_project.py 执行耗时")
def initialize_project() -> None:
    """Initialize the ODPlatform directory structure."""
    get_logger(
        base_path=LOGGING_DIR,
        log_type="init_project",
        temp_log=False,
    )

    logger.info("开始初始化项目核心目录".center(LINE_WIDTH, "="))
    logger.info("项目根目录: %s", ROOT_DIR)

    created: List[Path] = []
    existed: List[Path] = []

    for directory in get_dirs_to_initialize():
        rel_path = directory.relative_to(ROOT_DIR)
        if directory.exists():
            existed.append(directory)
            logger.info("目录已存在: %s", rel_path)
            continue

        try:
            directory.mkdir(parents=True, exist_ok=True)
            created.append(directory)
            logger.info("成功创建目录: %s", rel_path)
        except OSError as exc:
            logger.error("创建目录失败: %s: %s", rel_path, exc)
            raise SystemExit(1) from exc

    logger.info("初始化汇总".center(LINE_WIDTH, "="))
    logger.info(format_table_row(["目录", "状态"], TABLE_WIDTHS, TABLE_ALIGNS))
    logger.info(format_table_separator(TABLE_WIDTHS))

    for directory in created:
        logger.info(
            format_table_row(
                [str(directory.relative_to(ROOT_DIR)), "新创建"],
                TABLE_WIDTHS,
                TABLE_ALIGNS,
            )
        )

    for directory in existed:
        logger.info(
            format_table_row(
                [str(directory.relative_to(ROOT_DIR)), "已存在"],
                TABLE_WIDTHS,
                TABLE_ALIGNS,
            )
        )

    logger.info(format_table_separator(TABLE_WIDTHS))


if __name__ == "__main__":
    initialize_project()
