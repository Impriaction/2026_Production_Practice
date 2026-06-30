from pathlib import Path

import pytest

from ..cli import reset_project as reset_cli


def test_resolve_targets_runtime_does_not_include_raw_data():
    targets = reset_cli._resolve_targets("runtime")

    assert reset_cli.RAW_DATA_DIR not in targets
    assert reset_cli.LOGGING_DIR in targets


def test_validate_args_requires_force_for_full_scope():
    with pytest.raises(ValueError):
        reset_cli._validate_args(type("Args", (), {"scope": "full", "force": False})())


def test_expand_full_scope_skips_protected_children(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "data"
    models_dir = tmp_path / "models"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    pretrained_dir = models_dir / "pretrained"
    trained_dir = models_dir / "trained"
    scratch_dir = data_dir / "scratch"

    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    pretrained_dir.mkdir(parents=True)
    trained_dir.mkdir(parents=True)
    scratch_dir.mkdir(parents=True)

    monkeypatch.setattr(reset_cli, "DATA_DIR", data_dir)
    monkeypatch.setattr(reset_cli, "MODELS_DIR", models_dir)
    monkeypatch.setattr(reset_cli, "RAW_DATA_DIR", raw_dir)
    monkeypatch.setattr(reset_cli, "PRETRAINED_MODELS_DIR", pretrained_dir, raising=False)
    monkeypatch.setattr(
        reset_cli,
        "get_protected_reset_paths",
        lambda: (pretrained_dir, reset_cli.META_LOGGING_DIR),
    )

    expanded = reset_cli._expand_full_scope_targets([data_dir, models_dir, processed_dir, trained_dir, raw_dir])

    assert scratch_dir in expanded
    assert pretrained_dir not in expanded
