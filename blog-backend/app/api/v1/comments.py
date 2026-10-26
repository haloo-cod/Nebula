"""数据库账户化评论路由。"""

import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, security_scheme
from app.config import settings
from app.database import get_db
from app.models.comment import Comment
from app.models.user import User
from app.models.friend import Friend
from app.models.friend_application import FriendApplication
from app.schemas.comment import CommentCreate, CommentItem, CommentListResponse
from app.utils.security import decode_user_token
from app.services.analytics import hash_ip, get_client_ip
from app.services.rate_limit import enforce_event_limit
from app.services.friend import lock_application
from app.services.friend_application import require_public_application

router = APIRouter(prefix="/comments", tags=["评论"])


async def _optional_user(
    credentials: HTTPAuthorizationCredentials | None,
    db: AsyncSession,
) -> User | None:
    """评论读取接口可匿名访问，但登录后返回操作权限。"""

    if not credentials:
        return None
    payload = decode_user_token(credentials.credentials)
    if not payload:
        return None
    return await db.scalar(select(User).where(User.auth_id == payload["sub"], User.is_active.is_(True)))


def _comment_author(comment: Comment) -> str:
    """保留账户作者和历史匿名作者的显示名称。"""

    if comment.user:
        return comment.user.display_name or comment.user.username
    return comment.legacy_author or "已注销用户"


def _serialize_comment(
    comment: Comment,
    current_user: User | None,
    children: list[CommentItem],
    reply_to: Comment | None = None,
    *,
    is_root: bool = False,
) -> CommentItem:
    """展示层只有两级，回复仍保留数据库中的真实目标。"""

    return CommentItem(
        id=comment.id,
        user_id=comment.user_id,
        parent_id=None if is_root else comment.parent_id,
        reply_to_author=_comment_author(reply_to) if reply_to and not is_root else "",
        author=_comment_author(comment),
        date=comment.created_at.strftime("%Y-%m-%d %H:%M"),
        content=comment.content,
        avatar_url=comment.user.avatar_url if comment.user else "",
        avatar_color=comment.legacy_avatar_color,
        can_delete=bool(current_user and (current_user.is_admin or current_user.id == comment.user_id)),
        children=children,
    )


async def _comment_tree(page_key: str, current_user: User | None, db: AsyncSession) -> list[CommentItem]:
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.page_key == page_key)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
    )
    comments = list(result.scalars().unique().all())
    by_id = {comment.id: comment for comment in comments}
    children_by_parent: dict[int | None, list[Comment]] = {}
    for comment in comments:
        children_by_parent.setdefault(comment.parent_id, []).append(comment)

    roots: list[CommentItem] = []
    visited: set[int] = set()

    def append_thread(root: Comment) -> None:
        if root.id in visited:
            return
        visited.add(root.id)
        descendants: list[Comment] = []
        pending = list(children_by_parent.get(root.id, []))
        while pending:
            child = pending.pop()
            if child.id in visited:
                continue
            visited.add(child.id)
            descendants.append(child)
            pending.extend(children_by_parent.get(child.id, []))
        descendants.sort(key=lambda item: (item.created_at, item.id))
        replies = [
            _serialize_comment(child, current_user, [], by_id.get(child.parent_id))
            for child in descendants
        ]
        roots.append(_serialize_comment(root, current_user, replies, is_root=True))

    for comment in comments:
        if comment.parent_id is None or comment.parent_id not in by_id:
            append_thread(comment)
    # 无根的历史循环选择时间最早的节点作为展示根，不修改原始 parent_id。
    for comment in comments:
        append_thread(comment)
    roots.sort(key=lambda item: (by_id[item.id].created_at, item.id))
    return roots


@router.get("", response_model=CommentListResponse)
async def list_comments(
    page_key: str = Query(..., description="页面标识，如 about / post:slug"),
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """获取某页面评论，登录用户会额外获得本人评论的删除权限。"""

    await require_public_application(db, page_key)
    current_user = await _optional_user(credentials, db)
    items = await _comment_tree(page_key, current_user, db)
    total = (await db.execute(select(func.count()).select_from(Comment).where(Comment.page_key == page_key))).scalar() or 0
    return CommentListResponse(items=items, total=total)


@router.get("/count")
async def comment_count(page_key: str = Query(...), db: AsyncSession = Depends(get_db)):
    """获取某页面评论总数。"""

    await require_public_application(db, page_key)
    count = (await db.execute(select(func.count()).select_from(Comment).where(Comment.page_key == page_key))).scalar() or 0
    return {"page_key": page_key, "count": count}


class BatchCountRequest(BaseModel):
    """批量评论计数请求。"""

    page_keys: list[str]


@router.post("/batch-count")
async def batch_comment_count(body: BatchCountRequest, db: AsyncSession = Depends(get_db)):
    """批量获取多个页面评论总数。"""

    result = {key: 0 for key in body.page_keys}
    visible_keys = [key for key in body.page_keys if not key.startswith("friend-application:")]
    application_keys: dict[int, str] = {}
    for key in body.page_keys:
        match = re.fullmatch(r"friend-application:([1-9][0-9]*)", key)
        if match and len(match[1]) <= 19 and int(match[1]) <= 2**63 - 1:
            application_keys[int(match[1])] = key
    if application_keys:
        visible_ids = (await db.scalars(
            select(FriendApplication.id).join(Friend, Friend.id == FriendApplication.friend_id).where(
                FriendApplication.status == "approved", FriendApplication.id.in_(application_keys),
            )
        )).all()
        visible_keys.extend(application_keys[application_id] for application_id in visible_ids)
    if visible_keys:
        rows = await db.execute(
            select(Comment.page_key, func.count(Comment.id))
            .where(Comment.page_key.in_(visible_keys))
            .group_by(Comment.page_key)
        )
        result.update({key: count for key, count in rows.all()})
    return result


@router.post("", response_model=CommentItem, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CommentCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """以当前登录账户发表评论。"""

    if not user.email_verified and user.email and settings.REQUIRE_EMAIL_VERIFICATION:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="验证邮箱后才能发表评论")
    await enforce_event_limit(db, hash_ip(get_client_ip(request)), "comment_create", 3600, 20)
    if body.page_key.startswith("friend-application:"):
        match = re.fullmatch(r"friend-application:([1-9][0-9]*)", body.page_key)
        if not match or len(match[1]) > 19 or int(match[1]) > 2**63 - 1:
            raise HTTPException(404, "申请不存在或尚未公开")
        if not await lock_application(db, int(match[1]), approved_only=True):
            raise HTTPException(404, "申请不存在或尚未公开")
    await require_public_application(db, body.page_key)
    parent = None
    if body.parent_id is not None:
        parent = await db.scalar(
            select(Comment).options(selectinload(Comment.user)).where(Comment.id == body.parent_id)
        )
        if not parent or parent.page_key != body.page_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="回复的评论不存在")
    comment = Comment(page_key=body.page_key, user_id=user.id, parent_id=body.parent_id, content=body.content)
    comment.user = user
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return _serialize_comment(comment, user, [], parent)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """用户删除本人评论，管理员可删除任意评论。"""

    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    if not user.is_admin and comment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该评论")
    page_comments = (await db.scalars(
        select(Comment).where(Comment.page_key == comment.page_key)
    )).all()
    children_by_parent: dict[int | None, list[Comment]] = {}
    for row in page_comments:
        children_by_parent.setdefault(row.parent_id, []).append(row)
    visited: set[int] = set()
    descendants: list[Comment] = []
    pending = [comment]
    while pending:
        row = pending.pop()
        if row.id in visited:
            continue
        visited.add(row.id)
        descendants.append(row)
        pending.extend(children_by_parent.get(row.id, []))
    for row in reversed(descendants):
        await db.delete(row)
    await db.commit()
