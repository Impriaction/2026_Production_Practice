from __future__ import annotations

from od_platform.validate_dataset.checks._shared import load_snapshot_or_error
from od_platform.validate_dataset.registry import CheckContext, CheckResult, CheckSeverity, check


@check("split_uniqueness", order=40)
def validate_split_uniqueness(ctx: CheckContext) -> CheckResult:
    snapshot, error = load_snapshot_or_error(ctx, "split_uniqueness")
    if error is not None:
        return error

    train = snapshot.split_files["train"].image_stems
    val = snapshot.split_files["val"].image_stems
    test = snapshot.split_files["test"].image_stems

    overlaps = {
        "train_val": sorted(train & val),
        "train_test": sorted(train & test),
        "val_test": sorted(val & test),
    }
    overlap_pair_count = sum(1 for values in overlaps.values() if values)
    overlap_sample_count = sum(len(values) for values in overlaps.values())

    if overlap_pair_count:
        return CheckResult(
            name="split_uniqueness",
            severity=CheckSeverity.ERROR,
            summary=f"split 之间存在交叉泄露: {overlap_pair_count} 组交集, 共 {overlap_sample_count} 个重复样本",
            details={"reason": "split_overlap", "overlaps": overlaps},
        )

    return CheckResult(
        name="split_uniqueness",
        severity=CheckSeverity.INFO,
        summary="train/val/test 之间没有交叉样本",
        details={"overlaps": overlaps},
    )
