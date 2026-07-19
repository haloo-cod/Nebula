"""
评论 service — comments.json 读写（文件锁保护）

JSON 结构:
{
  "about": [
    { "id": 1, "author": "...", "date": "...", "content": "...", "avatar_color": "#xxx", "children": [...] }
  ],
  "post:slug": [...]
}
"""

import json
import random
import time
from pathlib import Path

from filelock import FileLock

from app.config import settings

COMMENTS_FILE = settings.DATA_DIR / "comments.json"
LOCK_FILE = settings.DATA_DIR / "comments.json.lock"

AVATAR_COLORS = [
    "#6366f1", "#ec4899", "#14b8a6", "#f59e0b",
    "#8b5cf6", "#06b6d4", "#ef4444", "#22c55e",
]


def _read_all() -> dict:
    if not COMMENTS_FILE.exists():
        return {}
    content = COMMENTS_FILE.read_text(encoding="utf-8")
    try:
        return json.loads(content) if content.strip() else {}
    except json.JSONDecodeError:
        return {}


def _write_all(data: dict) -> None:
    COMMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    COMMENTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _generate_id() -> int:
    return int(time.time() * 1000) + random.randint(0, 999)


def _format_date() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def get_comments_by_page_key(page_key: str) -> list[dict]:
    """获取某页面的全部评论（含嵌套回复）"""
    data = _read_all()
    return data.get(page_key, [])


def get_comment_count(page_key: str) -> int:
    """计算某页面评论总数（含回复）"""
    comments = get_comments_by_page_key(page_key)
    count = 0
    for c in comments:
        count += 1 + len(c.get("children", []))
    return count


def add_comment(page_key: str, author: str, content: str, parent_id: int | None = None) -> dict:
    """添加评论（支持回复）"""
    lock = FileLock(str(LOCK_FILE))
    with lock:
        data = _read_all()
        page_comments = data.get(page_key, [])

        new_comment = {
            "id": _generate_id(),
            "author": author,
            "date": _format_date(),
            "content": content,
            "avatar_color": random.choice(AVATAR_COLORS),
            "children": [],
        }

        if parent_id:
            # 找到父评论，追加为 child
            found = False
            for c in page_comments:
                if c["id"] == parent_id:
                    c.setdefault("children", []).append(new_comment)
                    found = True
                    break
            if not found:
                # 父评论不存在时降级为顶级
                page_comments.append(new_comment)
        else:
            page_comments.append(new_comment)

        data[page_key] = page_comments
        _write_all(data)

    return new_comment


def delete_comment(page_key: str, comment_id: int) -> bool:
    """删除评论（包括作为子评论的情况）"""
    lock = FileLock(str(LOCK_FILE))
    with lock:
        data = _read_all()
        page_comments = data.get(page_key, [])

        # 尝试删除顶级评论
        for i, c in enumerate(page_comments):
            if c["id"] == comment_id:
                page_comments.pop(i)
                data[page_key] = page_comments
                _write_all(data)
                return True
            # 尝试删除子评论
            children = c.get("children", [])
            for j, child in enumerate(children):
                if child["id"] == comment_id:
                    children.pop(j)
                    data[page_key] = page_comments
                    _write_all(data)
                    return True

    return False
