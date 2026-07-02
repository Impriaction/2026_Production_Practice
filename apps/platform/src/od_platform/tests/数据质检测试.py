from pathlib import Path

from od_platform.common.logging_utils import get_logger
from od_platform.common.paths import DATASET_CONFIGS_DIR, LOGGING_DIR
from od_platform.validate_dataset.registry import CheckContext, list_check_names
from od_platform.validate_dataset.service import run_all_checks


get_logger(
    base_path=LOGGING_DIR,
    log_type="数据质检测试",
    temp_log=False,
)

print(f"已经注册的check: {list_check_names()}")

ctx = CheckContext(yaml_path=DATASET_CONFIGS_DIR / "rsod.yaml")
results = run_all_checks(ctx)

for result in results:
    print(result.severity, result.name, "-", result.summary)
    if result.details.get("problems"):
        for problem in result.details["problems"]:
            print(f"  - {problem}")
