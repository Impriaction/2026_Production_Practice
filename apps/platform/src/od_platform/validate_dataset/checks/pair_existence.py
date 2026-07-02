from __future__ import annotations

from od_platform.validate_dataset.checks._shared import load_snapshot_or_error
from od_platform.validate_dataset.registry import CheckContext, CheckResult, CheckSeverity, check


@check("pair_existence", order=20)
def validate_pair_existence(ctx: CheckContext) -> CheckResult:
    snapshot, error = load_snapshot_or_error(ctx, "pair_existence")
    if error is not None:
        return error

    problems: list[str] = []
    split_stats: dict[str, dict[str, object]] = {}

    for split_name, split_files in snapshot.split_files.items():
        missing_labels = sorted(split_files.image_stems - split_files.label_stems)
        orphan_labels = sorted(split_files.label_stems - split_files.image_stems)

        if not split_files.images_dir_exists:
            problems.append(f"{split_name} 缺少图片目录: {split_files.images_dir}")
        if not split_files.labels_dir_exists:
            problems.append(f"{split_name} 缺少标签目录: {split_files.labels_dir}")
        if missing_labels:
            problems.append(f"{split_name} 有 {len(missing_labels)} 张图像缺少对应标签")
        if orphan_labels:
            problems.append(f"{split_name} 有 {len(orphan_labels)} 个孤儿标签文件")

        split_stats[split_name] = {
            "image_count": len(split_files.image_paths),
            "label_count": len(split_files.label_paths),
            "missing_labels": missing_labels,
            "orphan_labels": orphan_labels,
        }

    if problems:
        return CheckResult(
            name="pair_existence",
            severity=CheckSeverity.ERROR,
            summary=f"图像与标签配对检查失败: {len(problems)} 处问题",
            details={"reason": "pair_mismatch", "problems": problems, "splits": split_stats},
        )

    return CheckResult(
        name="pair_existence",
        severity=CheckSeverity.INFO,
        summary="图像与标签配对完整",
        details={"splits": split_stats},
    )
