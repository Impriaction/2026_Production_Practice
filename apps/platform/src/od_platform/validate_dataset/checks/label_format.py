from __future__ import annotations

from od_platform.validate_dataset.checks._shared import load_snapshot_or_error, load_yaml_doc_or_error
from od_platform.validate_dataset.registry import CheckContext, CheckResult, CheckSeverity, check

MAX_REPORTED_PROBLEMS = 50


@check("label_format", order=30)
def validate_label_format(ctx: CheckContext) -> CheckResult:
    cfg, yaml_error = load_yaml_doc_or_error(ctx, "label_format")
    if yaml_error is not None:
        return yaml_error

    snapshot, error = load_snapshot_or_error(ctx, "label_format")
    if error is not None:
        return error

    nc = cfg.get("nc")
    if not isinstance(nc, int) or nc <= 0:
        return CheckResult(
            name="label_format",
            severity=CheckSeverity.ERROR,
            summary="无法检查标签格式: yaml 中 nc 不合法",
            details={"reason": "invalid_nc", "nc": nc},
        )

    problems: list[str] = []
    bad_files: set[str] = set()
    bad_line_count = 0
    checked_label_count = 0

    for split_files in snapshot.split_files.values():
        for label_path in split_files.label_paths:
            checked_label_count += 1
            file_has_issue = False
            for line_no, raw_line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), 1):
                line = raw_line.strip()
                if not line:
                    continue

                fields = line.split()
                issue = _validate_label_line(fields, nc)
                if issue is None:
                    continue

                bad_line_count += 1
                file_has_issue = True
                if len(problems) < MAX_REPORTED_PROBLEMS:
                    problems.append(f"{label_path.name}:{line_no} - {issue}")

            if file_has_issue:
                bad_files.add(label_path.name)

    if problems:
        return CheckResult(
            name="label_format",
            severity=CheckSeverity.ERROR,
            summary=f"YOLO 标签格式检查失败: {bad_line_count} 行异常, {len(bad_files)} 个文件受影响",
            details={
                "reason": "invalid_label_format",
                "problems": problems,
                "bad_file_count": len(bad_files),
                "bad_line_count": bad_line_count,
                "checked_label_count": checked_label_count,
            },
        )

    return CheckResult(
        name="label_format",
        severity=CheckSeverity.INFO,
        summary=f"YOLO 标签格式正确 (检查 {checked_label_count} 个标签文件)",
        details={
            "bad_file_count": 0,
            "bad_line_count": 0,
            "checked_label_count": checked_label_count,
        },
    )


def _validate_label_line(fields: list[str], nc: int) -> str | None:
    if len(fields) != 5:
        return f"字段数必须为 5, 实际为 {len(fields)}"

    try:
        class_id = int(fields[0])
    except ValueError:
        return f"class_id 不是整数: {fields[0]}"

    if not 0 <= class_id < nc:
        return f"class_id 越界: {class_id}, 合法范围 [0, {nc})"

    coords: list[float] = []
    for token in fields[1:]:
        try:
            coords.append(float(token))
        except ValueError:
            return f"坐标不是浮点数: {token}"

    x, y, w, h = coords
    if not 0.0 <= x <= 1.0:
        return f"x 不在 [0,1] 内: {x}"
    if not 0.0 <= y <= 1.0:
        return f"y 不在 [0,1] 内: {y}"
    if not 0.0 <= w <= 1.0:
        return f"w 不在 [0,1] 内: {w}"
    if not 0.0 <= h <= 1.0:
        return f"h 不在 [0,1] 内: {h}"
    if w <= 0.0:
        return f"w 必须大于 0: {w}"
    if h <= 0.0:
        return f"h 必须大于 0: {h}"
    return None
