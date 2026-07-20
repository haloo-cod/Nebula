"""管理员用户管理 API。"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.user import AuthSession, User
from app.schemas.user import (
    UserAdminItem,
    UserAdminListResponse,
    UserAdminUpdate,
    UserPasswordReset,
)
from app.utils.security import hash_password

router = APIRouter(prefix="/users", tags=["用户管理"])


async def _get_user(user_id: int, db: AsyncSession) -> User:
    """按 ID 获取用户。"""

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user


async def _ensure_admin_survives(db: AsyncSession, current: User, target: User, next_is_admin: bool) -> None:
    """防止管理员误删自己或清空最后一个可用管理员。"""

    if current.id == target.id and not next_is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能取消自己的管理员权限")
    if target.is_admin and not next_is_admin:
        count = (await db.execute(select(func.count()).select_from(User).where(User.is_admin.is_(True), User.is_active.is_(True)))).scalar() or 0
        if count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少保留一个可用管理员")


async def _revoke_sessions(user_id: int, db: AsyncSession) -> None:
    """撤销用户全部刷新会话。"""

    await db.execute(
        AuthSession.__table__.update()
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )


@router.get("", response_model=UserAdminListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """分页搜索用户。"""

    stmt = select(User)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(User.username.ilike(pattern), User.email.ilike(pattern), User.display_name.ilike(pattern)))
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    result = await db.execute(stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return UserAdminListResponse(items=list(result.scalars().all()), total=total)


@router.get("/{user_id}", response_model=UserAdminItem)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    """获取用户详情。"""

    return await _get_user(user_id, db)


@router.put("/{user_id}", response_model=UserAdminItem)
async def update_user(
    user_id: int,
    data: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_admin),
):
    """修改用户资料、权限和状态。"""

    user = await _get_user(user_id, db)
    await _ensure_admin_survives(db, current, user, data.is_admin)
    if data.email:
        data.email = data.email.strip().lower()
        duplicate = (await db.execute(select(User).where(User.email == data.email, User.id != user_id))).scalar_one_or_none()
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已被其他用户使用")
    if user.is_active and not data.is_active:
        await _revoke_sessions(user.id, db)
    user.email = data.email
    user.display_name = data.display_name.strip()
    user.email_verified = data.email_verified
    user.is_admin = data.is_admin
    user.is_active = data.is_active
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    user_id: int,
    data: UserPasswordReset,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """重置密码并撤销旧会话。"""

    user = await _get_user(user_id, db)
    user.password_hash = hash_password(data.password)
    await _revoke_sessions(user.id, db)
    await db.commit()


@router.post("/{user_id}/revoke-sessions", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_sessions(user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    """撤销指定用户的全部登录会话。"""

    await _get_user(user_id, db)
    await _revoke_sessions(user_id, db)
    await db.commit()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_admin),
):
    """删除用户，评论因 SET NULL 保留为历史评论。"""

    user = await _get_user(user_id, db)
    if current.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己的账户")
    await _ensure_admin_survives(db, current, user, False)
    await db.delete(user)
    await db.commit()
