import logging
import sys
from functools import wraps
from datetime import datetime
from pathlib import Path
from time import perf_counter

LOGGER_NAME = "od_platform"
CONSOLE_FORMAT = "%(filename)-20s:%(lineno)4d | %(message)s"
FILE_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)


def _build_log_file(base_path: Path, log_type: str, temp_log: bool) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = "temp" if temp_log else timestamp
    return base_path / f"{log_type}_{suffix}.log"


def get_logger(
    base_path: Path,
    log_type: str = "app",
    temp_log: bool = False,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configure and return the shared od_platform logger."""
    base_path.mkdir(parents=True, exist_ok=True)
    log_file = _build_log_file(base_path, log_type, temp_log)

    logger = logging.getLogger(LOGGER_NAME)
    config_key = (str(log_file), level)
    current_key = getattr(logger, "_od_platform_config_key", None)
    if current_key == config_key and logger.handlers:
        return logger

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    logger.setLevel(level)
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT))

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger._od_platform_config_key = config_key
    logger.log_file = log_file
    return logger


def log_execution_time(
    logger_name: str = LOGGER_NAME,
    message: str = "执行耗时",
    level: int = logging.INFO,
):
    """Log the execution time of a function with a decorator."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = perf_counter() - start
                logger = logging.getLogger(logger_name)
                logger.log(level, "%s: %.3f 秒", message, elapsed)

        return wrapper

    return decorator
