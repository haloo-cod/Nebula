"""数据库账户化评论路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.schemas.comment import CommentCreate, CommentItem, CommentListResponse
from app.utils.security import decode_access_token

router = APIRouter(prefix="/comments", tags=["评论"])


async def _optional_user(
    credentials: HTTPAuthorizationCredentials | None,
    db: AsyncSession,
) -> User | None:
    """评论读取接口可匿名访问，但登录后返回操作权限。"""

    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    subject = payload.get("sub") if payload else None
    if not subject:
        return None
    condition = User.id == int(subject) if str(subject).isdigit() else User.username == subject
    return (await db.execute(select(User).where(condition))).scalar_one_or_none()


def _serialize_comment(comment: Comment, current_user: User | None, children: list[CommentItem]) -> CommentItem:
    """将 ORM 评论转换为前端树节点。"""

    author = comment.legacy_author
    avatar_url = ""
    if comment.user:
        author = comment.user.display_name or comment.user.username
        avatar_url = comment.user.avatar_url
    return CommentItem(
        id=comment.id,
        user_id=comment.user_id,
        author=author or "已注销用户",
        date=comment.created_at.strftime("%Y-%m-%d %H:%M"),
        content=comment.content,
        avatar_url=avatar_url,
        avatar_color=comment.legacy_avatar_color,
        can_delete=bool(current_user and (current_user.is_admin or current_user.id == comment.user_id)),
        children=children,
    )


async def _comment_tree(page_key: str, current_user: User | None, db: AsyncSession) -> list[CommentItem]:
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.page_key == page_key)
        .order_by(Comment.created_at.asc())
    )
    comments = list(result.scalars().unique().all())
    children_by_parent: dict[int | None, list[Comment]] = {}
    for comment in comments:
        children_by_parent.setdefault(comment.parent_id, []).append(comment)

    def build(parent_id: int | None) -> list[CommentItem]:
        return [
            _serialize_comment(comment, current_user, build(comment.id))
            for comment in children_by_parent.get(parent_id, [])
        ]

    return build(None)


@router.get("", response_model=CommentListResponse)
async def list_comments(
    page_key: str = Query(..., description="页面标识，如 about / post:slug"),
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """获取某页面评论，登录用户会额外获得本人评论的删除权限。"""

    current_user = await _optional_user(credentials, db)
    items = await _comment_tree(page_key, current_user, db)
    total = (await db.execute(select(func.count()).select_from(Comment).where(Comment.page_key == page_key))).scalar() or 0
    return CommentListResponse(items=items, total=total)


@router.get("/count")
async def comment_count(page_key: str = Query(...), db: AsyncSession = Depends(get_db)):
    """获取某页面评论总数。"""

    count = (await db.execute(select(func.count()).select_from(Comment).where(Comment.page_key == page_key))).scalar() or 0
    return {"page_key": page_key, "count": count}


class BatchCountRequest(BaseModel):
    """批量评论计数请求。"""

    page_keys: list[str]


@router.post("/batch-count")
async def batch_comment_count(body: BatchCountRequest, db: AsyncSession = Depends(get_db)):
    """批量获取多个页面评论总数。"""

    result = {key: 0 for key in body.page_keys}
    if body.page_keys:
        rows = await db.execute(
            select(Comment.page_key, func.count(Comment.id))
            .where(Comment.page_key.in_(body.page_keys))
            .group_by(Comment.page_key)
        )
        result.update({key: count for key, count in rows.all()})
    return result


@router.post("", response_model=CommentItem, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CommentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """以当前登录账户发表评论。"""

    if not user.email_verified and user.email and settings.REQUIRE_EMAIL_VERIFICATION:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="验证邮箱后才能发表评论")
    if body.parent_id:
        parent = await db.get(Comment, body.parent_id)
        if not parent or parent.page_key != body.page_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="回复的评论不存在")
    comment = Comment(page_key=body.page_key, user_id=user.id, parent_id=body.parent_id, content=body.content)
    comment.user = user
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return _serialize_comment(comment, user, [])


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
    descendants = [comment_id]
    for parent_id in descendants:
        child_ids = (
            await db.execute(select(Comment.id).where(Comment.parent_id == parent_id))
        ).scalars().all()
        descendants.extend(child_ids)
    rows = (await db.execute(select(Comment).where(Comment.id.in_(descendants)))).scalars().all()
    for row in reversed(rows):
        await db.delete(row)
    await db.commit()
