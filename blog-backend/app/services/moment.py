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
from datetime import datetime

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


def get_moments(page: int = 1, page_size: int = 10) -> tuple[list[dict], int]:
    """分页获取说说（按时间倒序）"""
    all_moments = _read_all()
    # 倒序排列
    all_moments.sort(key=lambda m: m.get("date", ""), reverse=True)
    total = len(all_moments)
    offset = (page - 1) * page_size
    items = all_moments[offset:offset + page_size]
    # 不返回 liked_ips
    for item in items:
        item.pop("liked_ips", None)
    return items, total


def get_moment_by_id(moment_id: int) -> dict | None:
    """获取单条说说"""
    for m in _read_all():
        if m.get("id") == moment_id:
            m.pop("liked_ips", None)
            return m
    return None


def create_moment(content: str, mood: str = "", tags: list[str] | None = None, images: list[str] | None = None) -> dict:
    """发布说说"""
    lock = FileLock(str(LOCK_FILE))
    with lock:
        data = _read_all()
        new_moment = {
            "id": _generate_id(),
            "date": datetime.now().isoformat(timespec="seconds"),
            "content": content,
            "mood": mood,
            "tags": tags or [],
            "images": images or [],
            "likes": 0,
            "liked_ips": [],
            "comments": [],
        }
        data.append(new_moment)
        _write_all(data)
    result = {k: v for k, v in new_moment.items() if k != "liked_ips"}
    return result


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
                comment = {
                    "id": _generate_id(),
                    "nickname": nickname,
                    "content": content,
                    "date": datetime.now().isoformat(timespec="seconds"),
                    "likes": 0,
                }
                m.setdefault("comments", []).append(comment)
                _write_all(data)
                return comment
    return None


def get_moment_comments(moment_id: int) -> list[dict]:
    """获取说说评论"""
    for m in _read_all():
        if m.get("id") == moment_id:
            return m.get("comments", [])
    return []
