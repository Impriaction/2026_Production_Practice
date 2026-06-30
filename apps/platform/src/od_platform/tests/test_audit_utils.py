import json
import zipfile
from pathlib import Path

from ..common.audit_utils import (
    build_audit_payload,
    create_backup_archive,
    summarize_paths,
    write_audit_log,
)


def test_summarize_paths_counts_files_and_bytes(tmp_path: Path):
    sample_dir = tmp_path / "sample"
    sample_dir.mkdir()
    (sample_dir / "a.txt").write_text("abc", encoding="utf-8")
    (sample_dir / "b.txt").write_text("hello", encoding="utf-8")

    summary = summarize_paths([sample_dir])

    assert summary["total_files"] == 2
    assert summary["total_bytes"] == 8


def test_create_backup_archive_creates_zip_with_relative_paths(tmp_path: Path):
    root_dir = tmp_path / "repo"
    target_dir = root_dir / "runs"
    target_dir.mkdir(parents=True)
    (target_dir / "artifact.txt").write_text("artifact", encoding="utf-8")

    archive_path = create_backup_archive([target_dir], root_dir, tmp_path / "backups", "runtime")

    assert archive_path.exists()
    with zipfile.ZipFile(archive_path) as archive:
        assert "runs/artifact.txt" in archive.namelist()


def test_write_audit_log_persists_json(tmp_path: Path):
    target = tmp_path / "runs"
    target.mkdir()
    summary = summarize_paths([target])
    payload = build_audit_payload(
        mode="preview",
        scope="runtime",
        dry_run=True,
        targets=[target],
        summary=summary,
        backup_archive=None,
    )

    audit_path = write_audit_log(tmp_path / "audit", payload)

    assert audit_path.exists()
    saved = json.loads(audit_path.read_text(encoding="utf-8"))
    assert saved["scope"] == "runtime"
    assert saved["dry_run"] is True
