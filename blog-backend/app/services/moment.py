"""
说说 service — moments.json 读写

JSON 结构（数组）:
[
  {
    "id": 1,
    "date": "2026-07-14T09:22:00",
    "content": "...",
    "mood": "开心",
    "tags": [],
    "images": [],
    "likes": 3,
    "liked_ips": ["127.0.0.1"],
    "comments": [
      { "id": 101, "nickname": "...", "content": "...", "date": "...", "likes": 0 }
    ]
  }
]
"""

import json
import random
import time
from datetime import datetime, timedelta, timezone

from filelock import FileLock

from app.config import settings

MOMENTS_FILE = settings.DATA_DIR / "moments.json"
LOCK_FILE = settings.DATA_DIR / "moments.json.lock"


def _read_all() -> list[dict]:
    if not MOMENTS_FILE.exists():
        return []
    content = MOMENTS_FILE.read_text(encoding="utf-8")
    try:
        data = json.loads(content) if content.strip() else []
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _write_all(data: list[dict]) -> None:
    MOMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    MOMENTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _generate_id() -> int:
    return int(time.time() * 1000) + random.randint(0, 999)


def _is_valid_ms_id(value: object) -> bool:
    """判断记录 ID 是否为合理的毫秒 Unix 时间戳。"""
    return isinstance(value, int) and not isinstance(value, bool) and 1_000_000_000_000 <= value < 10_000_000_000_000


def _utc_timestamp(record_id: int) -> str:
    """按毫秒 ID 中的 Unix 时间生成 UTC ISO 时间字符串。"""
    return datetime.fromtimestamp(record_id / 1000, timezone.utc).isoformat(timespec="seconds")


def _normalize_record_dates(record: dict) -> dict:
    """兼容旧 JSON 与缺省正文：说说和评论的毫秒 ID 是创建时间权威来源。"""
    normalized = dict(record)
    if not isinstance(normalized.get("content"), str):
        normalized["content"] = ""
    if _is_valid_ms_id(normalized.get("id")):
        normalized["date"] = _utc_timestamp(normalized["id"])
    comments = normalized.get("comments")
    if isinstance(comments, list):
        normalized["comments"] = [
            {
                **comment,
                "content": comment["content"] if isinstance(comment.get("content"), str) else "",
                "date": (
                    _utc_timestamp(comment["id"])
                    if _is_valid_ms_id(comment.get("id"))
                    else comment.get("date", "")
                ),
            }
            if isinstance(comment, dict)
            else comment
            for comment in comments
        ]
    return normalized


def get_moments(page: int = 1, page_size: int = 10) -> tuple[list[dict], int]:
    """分页获取说说，统一将历史时间按记录 ID 规范为 UTC。"""
    all_moments = [_normalize_record_dates(moment) for moment in _read_all()]
    all_moments.sort(key=lambda m: m.get("date", ""), reverse=True)
    total = len(all_moments)
    offset = (page - 1) * page_size
    items = all_moments[offset:offset + page_size]
    for item in items:
        item.pop("liked_ips", None)
    return items, total


def get_moment_activity_dates() -> tuple[set[str], int]:
    """获取按北京时间规范后的说说创建日期，供主页活跃天数统计。"""
    moments = [_normalize_record_dates(moment) for moment in _read_all()]
    dates = {
        datetime.fromtimestamp(moment["id"] / 1000, timezone.utc)
        .astimezone(timezone(timedelta(hours=8)))
        .date()
        .isoformat()
        for moment in moments
        if _is_valid_ms_id(moment.get("id"))
    }
    return dates, len(moments)


def get_moment_by_id(moment_id: int) -> dict | None:
    """获取按 UTC 规范时间返回的单条说说。"""
    for moment in _read_all():
        if moment.get("id") == moment_id:
            moment = _normalize_record_dates(moment)
            moment.pop("liked_ips", None)
            return moment
    return None

def create_moment(
    content: str,
    mood: str = "",
    mood_text: str = "",
    tags: list[str] | None = None,
    images: list[str] | None = None,
) -> dict:
    """发布说说"""
    lock = FileLock(str(LOCK_FILE))
    with lock:
        data = _read_all()
        moment_id = _generate_id()
        new_moment = {
            "id": moment_id,
            "date": _utc_timestamp(moment_id),
            "content": content,
            "mood": mood,
            "mood_text": mood_text,
            "tags": tags or [],
            "images": images or [],
            "likes": 0,
            "liked_ips": [],
            "comments": [],
        }
        data.append(new_moment)
        _write_all(data)
    return _normalize_record_dates({k: v for k, v in new_moment.items() if k != "liked_ips"})

def delete_moment(moment_id: int) -> bool:
    """删除说说"""
    lock = FileLock(str(LOCK_FILE))
    with lock:
        data = _read_all()
        for i, m in enumerate(data):
            if m.get("id") == moment_id:
                data.pop(i)
                _write_all(data)
                return True
    return False


def update_moment(
    moment_id: int,
    content: str,
    mood: str = "",
    mood_text: str = "",
    tags: list[str] | None = None,
    images: list[str] | None = None,
) -> dict | None:
    """更新说说内容，保留发布时间、点赞、评论和点赞记录。"""
    lock = FileLock(str(LOCK_FILE))
    with lock:
        data = _read_all()
        for moment in data:
            if moment.get("id") != moment_id:
                continue
            moment["content"] = content
            moment["mood"] = mood
            moment["mood_text"] = mood_text
            moment["tags"] = tags or []
            moment["images"] = images or []
            _write_all(data)
            return _normalize_record_dates({key: value for key, value in moment.items() if key != "liked_ips"})
    return None


def like_moment(moment_id: int, visitor_ip: str) -> int:
    """点赞说说（同一 IP 只记一次），返回最新点赞数"""
    lock = FileLock(str(LOCK_FILE))
    with lock:
        data = _read_all()
        for m in data:
            if m.get("id") == moment_id:
                liked_ips = m.setdefault("liked_ips", [])
                if visitor_ip not in liked_ips:
                    liked_ips.append(visitor_ip)
                    m["likes"] = m.get("likes", 0) + 1
                _write_all(data)
                return m["likes"]
    return 0


def add_moment_comment(moment_id: int, nickname: str, content: str) -> dict | None:
    """给说说添加评论"""
    lock = FileLock(str(LOCK_FILE))
    with lock:
        data = _read_all()
        for m in data:
            if m.get("id") == moment_id:
                comment_id = _generate_id()
                comment = {
                    "id": comment_id,
                    "nickname": nickname,
                    "content": content,
                    "date": _utc_timestamp(comment_id),
                    "likes": 0,
                }
                m.setdefault("comments", []).append(comment)
                _write_all(data)
                return _normalize_record_dates(comment)
    return None


def get_moment_comments(moment_id: int) -> list[dict] | None:
    for moment in _read_all():
        if moment.get("id") == moment_id:
            normalized = _normalize_record_dates(moment)
            return normalized.get("comments", [])
    return None


def delete_moment_comment(moment_id: int, comment_id: int) -> bool | None:
    """删除指定说说中的评论；说说不存在时返回 None。"""
    lock = FileLock(str(LOCK_FILE))
    with lock:
        data = _read_all()
        for moment in data:
            if moment.get("id") != moment_id:
                continue
            comments = moment.setdefault("comments", [])
            for index, comment in enumerate(comments):
                if comment.get("id") == comment_id:
                    comments.pop(index)
                    _write_all(data)
                    return True
            return False
    return None
