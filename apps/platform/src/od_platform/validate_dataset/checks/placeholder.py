from od_platform.validate_dataset.registry import (
    CheckContext,
    CheckResult,
    CheckSeverity,
    check,
)


@check("冒烟测试")
def placeholder_check(ctx: CheckContext) -> CheckResult:
    """冒烟测试。"""

    return CheckResult(
        name="冒烟测试",
        severity=CheckSeverity.PASS,
        summary="冒烟测试-用于检测注册表机制是否工作正常",
        details={"yaml_path": str(ctx.yaml_path)},
    )
