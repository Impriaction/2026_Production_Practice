from pathlib import Path

from ..common.paths import (
    LOGGING_DIR,
    META_LOGGING_DIR,
    PRETRAINED_MODELS_DIR,
    RAW_DATA_DIR,
    ROOT_DIR,
    get_dirs_to_reset,
    get_protected_reset_paths,
    is_protected_reset_path,
)


def test_runtime_scope_contains_expected_directories():
    runtime_dirs = get_dirs_to_reset("runtime")
    runtime_plus_raw_dirs = get_dirs_to_reset("runtime-plus-raw")

    assert LOGGING_DIR in runtime_dirs
    assert RAW_DATA_DIR not in runtime_dirs
    assert RAW_DATA_DIR in runtime_plus_raw_dirs


def test_protected_reset_paths_contain_safety_boundaries():
    protected_paths = get_protected_reset_paths()

    assert ROOT_DIR in protected_paths
    assert PRETRAINED_MODELS_DIR in protected_paths
    assert META_LOGGING_DIR in protected_paths


def test_is_protected_reset_path_respects_children_of_protected_paths(tmp_path: Path):
    protected = (tmp_path / "protected",)
    protected_child = protected[0] / "child.txt"
    protected[0].mkdir()
    protected_child.write_text("x", encoding="utf-8")

    assert is_protected_reset_path(protected[0], protected)
    assert is_protected_reset_path(protected_child, protected)
    assert not is_protected_reset_path(tmp_path / "safe", protected)
