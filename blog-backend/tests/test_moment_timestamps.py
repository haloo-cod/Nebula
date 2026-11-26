"""说说 JSON 时间规范化的边界和迁移安全回归。"""

import json
from pathlib import Path

import pytest

from app.schemas.moment import MomentCommentResponse, MomentListResponse, MomentResponse
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


def test_create_moment_and_comment_persist_required_fields(tmp_path: Path, monkeypatch):
    path = tmp_path / "moments.json"
    lock_path = tmp_path / "moments.json.lock"
    monkeypatch.setattr(service, "MOMENTS_FILE", path)
    monkeypatch.setattr(service, "LOCK_FILE", lock_path)

    created = service.create_moment(
        content="终于修好了",
        mood="😆",
        mood_text="开心",
        tags=["修复"],
        images=["/uploads/images/2026/11/a.png"],
    )
    validated = MomentResponse.model_validate(created)
    assert validated.content == "终于修好了"
    assert validated.mood_text == "开心"

    saved = json.loads(path.read_text("utf-8"))
    assert saved[0]["content"] == "终于修好了"
    assert saved[0]["date"] == created["date"]

    comment = service.add_moment_comment(created["id"], "Starlit", "测试评论")
    assert comment is not None
    validated_comment = MomentCommentResponse.model_validate(comment)
    assert validated_comment.content == "测试评论"
    assert validated_comment.likes == 0

    items, total = service.get_moments(page=1, page_size=5)
    response = MomentListResponse(items=items, total=total)
    assert response.total == 1
    assert response.items[0].content == "终于修好了"
    assert len(response.items[0].comments) == 1


def test_get_moments_tolerates_legacy_record_missing_content(tmp_path: Path, monkeypatch):
    path = tmp_path / "moments.json"
    path.write_text(json.dumps([
        {
            "id": 1795634884322,
            "date": "2026-11-25T19:28:04+00:00",
            "mood": "😭",
            "mood_text": "好累，感觉要猝了",
            "tags": [],
            "images": [],
            "likes": 0,
            "liked_ips": [],
            "comments": [],
        },
    ], ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(service, "MOMENTS_FILE", path)

    items, total = service.get_moments(page=1, page_size=5)
    response = MomentListResponse(items=items, total=total)
    assert response.total == 1
    assert response.items[0].id == 1795634884322
    assert response.items[0].content == ""

    one = service.get_moment_by_id(1795634884322)
    assert one is not None
    assert MomentResponse.model_validate(one).content == ""
