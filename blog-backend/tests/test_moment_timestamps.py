"""说说 JSON 时间规范化的边界和迁移安全回归。"""

import json
from pathlib import Path

import pytest

from app.services import moment as service
from scripts.migrate_moment_timestamps import migrate, normalize_records, timestamp_from_id


def test_timestamp_from_id_is_utc_and_rejects_non_millisecond_ids():
    assert timestamp_from_id(1795288541603) == "2026-11-21T19:15:41+00:00"
    assert timestamp_from_id(True) is None
    assert timestamp_from_id(1234) is None


def test_normalize_records_repairs_mixed_timezone_values_without_mutating_input():
    source = [{
        "id": 1795288541603,
        "date": "2026-11-22T03:15:41",
        "content": "keep",
        "comments": [{"id": 1788048684471, "date": "2026-08-30T08:11:23", "content": "keep"}],
    }]
    normalized, changed, skipped = normalize_records(source)
    assert changed == 2 and skipped == 0
    assert normalized[0]["date"] == "2026-11-21T19:15:41+00:00"
    assert normalized[0]["comments"][0]["date"] == "2026-08-30T00:11:24+00:00"
    assert source[0]["date"] == "2026-11-22T03:15:41"
    assert normalized[0]["content"] == "keep"


def test_migration_preview_is_read_only_and_apply_creates_backup(tmp_path: Path):
    path = tmp_path / "moments.json"
    original = json.dumps([{"id": 1795288541603, "date": "wrong", "comments": []}], ensure_ascii=False).encode()
    path.write_bytes(original)

    changed, skipped, backup = migrate(path)
    assert (changed, skipped, backup) == (1, 0, None)
    assert path.read_bytes() == original

    changed, skipped, backup = migrate(path, apply=True)
    assert changed == 1 and skipped == 0
    assert backup is not None and backup.read_bytes() == original
    saved = json.loads(path.read_text("utf-8"))
    assert saved[0]["date"] == "2026-11-21T19:15:41+00:00"
    assert not list(tmp_path.glob(".moments.json.*.tmp"))


def test_service_reads_mixed_dates_as_utc_and_activity_as_shanghai(tmp_path: Path, monkeypatch):
    path = tmp_path / "moments.json"
    path.write_text(json.dumps([
        {"id": 1795288541603, "date": "2026-11-22T03:15:41", "comments": []},
        {"id": 1792000585491, "date": "2026-10-15T01:56:24", "comments": []},
    ]), encoding="utf-8")
    monkeypatch.setattr(service, "MOMENTS_FILE", path)

    items, total = service.get_moments()
    assert total == 2
    assert [item["date"] for item in items] == [
        "2026-11-21T19:15:41+00:00",
        "2026-10-14T17:56:25+00:00",
    ]
    assert service.get_moment_activity_dates() == ({"2026-11-22", "2026-10-15"}, 2)
    assert "2026-11-22T03:15:41" in path.read_text("utf-8")


def test_default_migration_uses_configured_data_dir(tmp_path, monkeypatch, capsys):
    from app.config import settings

    data_dir = tmp_path / "production-data"
    data_dir.mkdir()
    path = data_dir / "moments.json"
    path.write_text(json.dumps([{"id": 1795288541603, "date": "wrong"}]), encoding="utf-8")
    monkeypatch.setattr(settings, "DATA_DIR", data_dir)
    monkeypatch.setattr("sys.argv", ["migrate_moment_timestamps"])

    from scripts import migrate_moment_timestamps

    migrate_moment_timestamps.main()

    assert "mode=preview changed_dates=1 skipped_invalid_ids=0" in capsys.readouterr().out
    assert json.loads(path.read_text("utf-8"))[0]["date"] == "wrong"
