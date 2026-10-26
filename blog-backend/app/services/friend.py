"""正式友链暂存变更及数据库提交后的公开 JSON 副本。"""

import asyncio
import json
import uuid
from pathlib import Path

from fastapi import HTTPException
from filelock import AsyncFileLock
from pydantic import HttpUrl, TypeAdapter, ValidationError
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.comment import Comment
from app.models.friend import Friend
from app.models.friend_application import FriendApplication
from app.schemas.friend import FriendApplicationCreate, FriendResponse


async def list_friends(db: AsyncSession) -> list[Friend]:
    """按稳定顺序读取正式友链。"""
    return list((await db.scalars(select(Friend).order_by(Friend.sort_order, Friend.id))).all())


def site_key(url: str) -> str:
    """标准化站点用于去重，保留路径大小写和查询参数。"""
    return str(TypeAdapter(HttpUrl).validate_python(url)).split("#", 1)[0]


async def require_new_friend_site(db: AsyncSession, url: str, exclude_id: int | None = None) -> None:
    """忽略无法解析的旧数据，禁止与现有正式站点重复。"""
    key = site_key(url)
    for friend_id, existing_url in (await db.execute(select(Friend.id, Friend.url))).all():
        if friend_id == exclude_id:
            continue
        try:
            existing_key = site_key(existing_url)
        except (ValueError, ValidationError):
            continue
        if existing_key == key:
            raise HTTPException(409, "该站点已在友链中")


async def flush_friend_changes(db: AsyncSession) -> None:
    """唯一约束失败必须回滚整个友链事务。"""
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "该站点已有待审核或已通过的申请") from exc


async def lock_application(db: AsyncSession, application_id: int, *, approved_only: bool = False) -> bool:
    """无字段变化的写入使评论创建与申请删除串行，保留更新时间。"""
    statement = update(FriendApplication).where(FriendApplication.id == application_id)
    if approved_only:
        statement = statement.where(FriendApplication.status == "approved", FriendApplication.friend_id.is_not(None))
    result = await db.execute(statement.values(
        id=FriendApplication.id, updated_at=FriendApplication.updated_at,
    ).execution_options(synchronize_session=False))
    return result.rowcount > 0


async def create_friend(
    db: AsyncSession, name: str, url: str, bio: str = "", avatar: str = "",
    sort_order: int = 0, rss_url: str = "",
) -> Friend:
    """暂存正式友链；事务由调用方提交。"""
    friend = Friend(name=name, bio=bio, avatar=avatar, url=url, sort_order=sort_order, rss_url=rss_url)
    db.add(friend)
    await db.flush()
    return friend


async def update_friend(
    db: AsyncSession, friend_id: int, name: str | None = None, bio: str | None = None,
    avatar: str | None = None, url: str | None = None, sort_order: int | None = None,
    rss_url: str | None = None,
) -> Friend | None:
    """编辑正式友链，申请来源站点在同一事务内同步公开字段。"""
    application_id = await db.scalar(select(FriendApplication.id).where(FriendApplication.friend_id == friend_id))
    if application_id is not None:
        await lock_application(db, application_id)
    friend = await db.get(Friend, friend_id, populate_existing=True)
    if friend is None:
        return None
    application = await db.get(FriendApplication, application_id, populate_existing=True) if application_id else None
    changes = {key: value for key, value in dict(
        name=name, bio=bio, avatar=avatar, url=url, sort_order=sort_order, rss_url=rss_url,
    ).items() if value is not None}
    if application:
        try:
            validated = FriendApplicationCreate(
                name=changes.get("name", friend.name), url=changes.get("url", friend.url),
                avatar=changes.get("avatar", friend.avatar), rss_url=changes.get("rss_url", friend.rss_url),
                email=application.email,
            )
        except ValidationError as exc:
            raise HTTPException(422, exc.errors(include_context=False)) from exc
        await require_new_friend_site(db, validated.url, exclude_id=friend_id)
        for field in ("name", "url", "avatar", "rss_url"):
            changes[field] = getattr(validated, field)
            setattr(application, field, changes[field])
        application.active_site_key = site_key(validated.url)
    for field, value in changes.items():
        setattr(friend, field, value)
    await flush_friend_changes(db)
    return friend


async def delete_friend(db: AsyncSession, friend_id: int) -> bool:
    """锁定关联申请后，显式清理全部讨论与申请，再删除正式友链。"""
    application_id = await db.scalar(select(FriendApplication.id).where(FriendApplication.friend_id == friend_id))
    if application_id is not None:
        await lock_application(db, application_id)
        await db.execute(delete(Comment).where(Comment.page_key == f"friend-application:{application_id}"))
        await db.execute(delete(FriendApplication).where(FriendApplication.id == application_id))
    friend = await db.get(Friend, friend_id, populate_existing=True)
    if friend is None:
        return False
    await db.delete(friend)
    await db.flush()
    return True


def _replace_snapshot(temp_file: Path, target: Path, content: str) -> None:
    """同目录临时文件原子替换；失败保留旧文件并清理临时文件。"""
    try:
        temp_file.write_text(content, encoding="utf-8", newline="\n")
        temp_file.replace(target)
    finally:
        temp_file.unlink(missing_ok=True)


async def sync_friends_json(db: AsyncSession) -> None:
    """锁内新会话读取最新已提交列表，数据库始终是唯一数据源。"""
    await asyncio.to_thread(settings.DATA_DIR.mkdir, parents=True, exist_ok=True)
    target = settings.DATA_DIR / "friends.json"
    async with AsyncFileLock(str(settings.DATA_DIR / "friends.json.lock"), timeout=10):
        async with AsyncSession(bind=db.bind) as snapshot_session:
            items = await list_friends(snapshot_session)
            content = json.dumps(
                [FriendResponse.model_validate(item).model_dump(mode="json") for item in items],
                ensure_ascii=False, indent=2,
            ) + "\n"
        temp_file = settings.DATA_DIR / f".friends.{uuid.uuid4().hex}.tmp"
        await asyncio.to_thread(_replace_snapshot, temp_file, target, content)


async def commit_friend_changes(db: AsyncSession) -> None:
    """提交成功后等待文件同步；文件失败不撤销已经保存的数据库结果。"""
    await db.commit()
    try:
        await sync_friends_json(db)
    except Exception as exc:
        raise HTTPException(503, "FRIEND_JSON_SYNC_FAILED") from exc
