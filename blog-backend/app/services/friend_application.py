"""友链申请状态机、审核与讨论可见性校验。"""

import re
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.friend import Friend
from app.models.friend_application import FriendApplication
from app.models.user import User
from app.schemas.friend import FriendApplicationCreate
from app.services.friend import (
    create_friend,
    delete_friend,
    flush_friend_changes,
    lock_application,
    require_new_friend_site,
    site_key,
)

ApplicationScope = Literal["public", "mine", "admin"]
ApplicationStatus = Literal["pending", "approved", "rejected"]
ReviewDecision = Literal["approved", "rejected"]

_APPLICATION_PAGE_KEY = re.compile(r"friend-application:([1-9][0-9]*)")
_MAX_SQLITE_INT = 2**63 - 1
_PUBLIC_APPLICATION_MISSING = "申请不存在或尚未公开"


async def create_application(
    db: AsyncSession, user: User, data: FriendApplicationCreate,
) -> FriendApplication:
    """以当前账户暂存待审核申请；事务由调用方提交。"""
    # 在写入前锁定认证时的账户版本，防止删除后的 SQLite ID 复用转移私有数据。
    active = await db.scalar(
        update(User).where(
            User.id == user.id, User.auth_id == user.auth_id,
        ).values(id=User.id, updated_at=User.updated_at)
        .returning(User.is_active).execution_options(synchronize_session=False)
    )
    if active is None:
        raise HTTPException(401, "用户不存在")
    if not active:
        raise HTTPException(403, "账户已被禁用")
    await require_new_friend_site(db, data.url)
    application = FriendApplication(
        user_id=user.id,
        name=data.name,
        url=data.url,
        avatar=data.avatar,
        email=str(data.email),
        rss_url=data.rss_url,
        status="pending",
        active_site_key=site_key(data.url),
    )
    db.add(application)
    await flush_friend_changes(db)
    return application


async def list_applications(
    db: AsyncSession,
    *,
    scope: ApplicationScope,
    user_id: int | None,
    status: ApplicationStatus | None,
    page: int,
    page_size: int,
) -> tuple[list[FriendApplication], int]:
    """公开区仅返回 approved 且仍关联正式友链的记录。"""
    if scope == "public":
        conditions = [FriendApplication.status == "approved"]
        statement = select(FriendApplication).join(Friend, Friend.id == FriendApplication.friend_id)
        count_statement = select(func.count(FriendApplication.id)).join(
            Friend, Friend.id == FriendApplication.friend_id,
        )
        ordering = (FriendApplication.reviewed_at.desc(), FriendApplication.id.desc())
    else:
        if scope == "mine":
            if user_id is None:
                return [], 0
            conditions = [FriendApplication.user_id == user_id]
        elif scope == "admin":
            conditions = [] if status is None else [FriendApplication.status == status]
        else:
            raise ValueError(f"未知的申请列表范围: {scope}")
        statement = select(FriendApplication)
        count_statement = select(func.count(FriendApplication.id))
        ordering = (FriendApplication.created_at.desc(), FriendApplication.id.desc())
    statement = statement.where(*conditions)
    count_statement = count_statement.where(*conditions)
    total = (await db.execute(count_statement)).scalar() or 0
    items = list((await db.scalars(
        statement.order_by(*ordering).offset((page - 1) * page_size).limit(page_size)
    )).all())
    return items, total


async def review_application(
    db: AsyncSession,
    application_id: int,
    decision: ReviewDecision,
    reason: str,
) -> FriendApplication:
    """仅 pending 可转换；条件 UPDATE 命中即取得写锁。"""
    now = datetime.now(timezone.utc)
    locked = await db.execute(
        update(FriendApplication)
        .where(FriendApplication.id == application_id, FriendApplication.status == "pending")
        .values(reviewed_at=now)
        .execution_options(synchronize_session=False)
    )
    if locked.rowcount == 0:
        application = await db.get(FriendApplication, application_id, populate_existing=True)
        if application is None:
            raise HTTPException(404, "申请不存在")
        if decision == "approved" and application.status == "approved":
            return application
        raise HTTPException(409, "申请已处理，请刷新列表")

    application = await db.get(FriendApplication, application_id, populate_existing=True)
    if application is None:
        await db.rollback()
        raise HTTPException(404, "申请不存在")

    if decision == "approved":
        try:
            await require_new_friend_site(db, application.url)
            latest_sort = await db.scalar(select(func.max(Friend.sort_order)))
            friend = await create_friend(
                db,
                name=application.name,
                url=application.url,
                bio="",
                avatar=application.avatar,
                sort_order=0 if latest_sort is None else latest_sort + 1,
                rss_url=application.rss_url,
            )
            application.status = "approved"
            application.friend_id = friend.id
            application.review_note = ""
            await flush_friend_changes(db)
        except HTTPException:
            await db.rollback()
            raise
        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(409, "该站点已有待审核或已通过的申请") from exc
        return application

    application.status = "rejected"
    application.review_note = reason
    application.active_site_key = None
    await flush_friend_changes(db)
    return application


async def delete_application(db: AsyncSession, application_id: int) -> bool:
    """先锁申请再清理讨论；已通过记录沿用正式友链删除流程。"""
    state = (await db.execute(
        select(FriendApplication.status, FriendApplication.friend_id)
        .where(FriendApplication.id == application_id)
    )).one_or_none()
    if state is None:
        return False
    if state.status == "approved" and state.friend_id is not None:
        return await delete_friend(db, state.friend_id)
    if not await lock_application(db, application_id):
        return False

    state = (await db.execute(
        select(FriendApplication.status, FriendApplication.friend_id)
        .where(FriendApplication.id == application_id)
    )).one_or_none()
    if state is None:
        return False
    if state.status == "approved" and state.friend_id is not None:
        return await delete_friend(db, state.friend_id)

    await db.execute(delete(Comment).where(Comment.page_key == f"friend-application:{application_id}"))
    await db.execute(delete(FriendApplication).where(FriendApplication.id == application_id))
    await db.flush()
    return True


async def require_public_application(db: AsyncSession, page_key: str) -> None:
    """申请讨论只对已通过且仍关联正式友链的记录开放。"""
    if not page_key.startswith("friend-application:"):
        return
    match = _APPLICATION_PAGE_KEY.fullmatch(page_key)
    if match is None or len(match.group(1)) > 19:
        raise HTTPException(404, _PUBLIC_APPLICATION_MISSING)
    application_id = int(match.group(1))
    if application_id > _MAX_SQLITE_INT:
        raise HTTPException(404, _PUBLIC_APPLICATION_MISSING)
    visible_id = await db.scalar(
        select(FriendApplication.id)
        .join(Friend, Friend.id == FriendApplication.friend_id)
        .where(
            FriendApplication.id == application_id,
            FriendApplication.status == "approved",
        )
    )
    if visible_id is None:
        raise HTTPException(404, _PUBLIC_APPLICATION_MISSING)
