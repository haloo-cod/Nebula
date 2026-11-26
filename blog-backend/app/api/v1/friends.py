"""
友链路由 — 公开列表 + 管理员 CRUD
"""

import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.models.friend_application import FriendApplication
from app.schemas.friend import (
    FriendCreate,
    FriendListResponse,
    FriendResponse,
    FriendUpdate,
    FriendExchangeInfo,
    FriendApplicationCreate,
    FriendApplicationReview,
    FriendApplicationPublic,
    FriendApplicationPrivate,
    FriendApplicationListResponse,
    FriendApplicationPrivateListResponse,
)
from app.models.site_config import SiteConfig
from app.services.friend_exchange import EXCHANGE_CONFIG_KEY, load_exchange_info
from app.services.friend import (
    create_friend,
    delete_friend,
    list_friends,
    update_friend,
    commit_friend_changes,
    sync_friends_json,
    lock_application,
)
from app.services.friend_application import (
    create_application, list_applications, review_application, delete_application,
)

router = APIRouter(prefix="/friends", tags=["友链"])

def default_exchange_info() -> FriendExchangeInfo:
    """返回交换友链的默认展示内容。"""
    return FriendExchangeInfo(
        name="你的站点名称",
        url="https://example.com",
        avatar="https://api.dicebear.com/9.x/adventurer/svg?seed=myblog",
        bio="这里填写你的站点简介。",
        requirements=["原创内容优先", "站点稳定可访问", "无违法违规内容", "最好有定期更新"],
        contact="your-email@example.com",
    )


@router.get("/exchange-info", response_model=FriendExchangeInfo)
async def get_exchange_info(db: AsyncSession = Depends(get_db)):
    """获取交换友链展示信息。"""
    return await load_exchange_info(db) or default_exchange_info()


@router.put("/exchange-info", response_model=FriendExchangeInfo)
async def update_exchange_info(
    data: FriendExchangeInfo,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新交换友链展示信息。"""
    result = await db.execute(select(SiteConfig).where(SiteConfig.key == EXCHANGE_CONFIG_KEY))
    config = result.scalar_one_or_none()
    value = json.dumps(data.model_dump(), ensure_ascii=False)
    if config:
        config.value = value
    else:
        db.add(SiteConfig(key=EXCHANGE_CONFIG_KEY, value=value, description="交换友链展示信息"))
    await db.commit()
    return data


@router.post("/sync-json", status_code=status.HTTP_204_NO_CONTENT)
async def rebuild_friends_json(
    db: AsyncSession = Depends(get_db), _: User = Depends(require_admin),
):
    """仅重建公开副本，不重复数据库写操作。"""
    try:
        await sync_friends_json(db)
    except Exception as exc:
        raise HTTPException(503, "FRIEND_JSON_SYNC_FAILED") from exc


@router.get("", response_model=FriendListResponse)
async def get_friends(db: AsyncSession = Depends(get_db)):
    """获取友链列表（公开接口）"""
    items = await list_friends(db)
    return FriendListResponse(items=items, total=len(items))


@router.post("", response_model=FriendResponse, status_code=status.HTTP_201_CREATED)
async def add_friend(
    data: FriendCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """添加友链（管理员）"""
    friend = await create_friend(
        db, name=data.name, bio=data.bio, avatar=data.avatar, url=data.url, sort_order=data.sort_order,
        rss_url=data.rss_url,
    )
    await commit_friend_changes(db)
    return friend


@router.post("/applications", response_model=FriendApplicationPrivate, status_code=201)
async def submit_application(
    data: FriendApplicationCreate, user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """唯一的申请提交入口，仅接收站点与联络字段。"""
    application = await create_application(db, user, data)
    await db.commit()
    return application


@router.get("/applications", response_model=FriendApplicationListResponse)
async def public_applications(
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """匿名可读，响应模型明确排除所有私有字段。"""
    items, total = await list_applications(db, scope="public", user_id=None, status=None, page=page, page_size=page_size)
    return FriendApplicationListResponse(items=[FriendApplicationPublic.model_validate(item) for item in items], total=total)


@router.get("/applications/mine", response_model=FriendApplicationPrivateListResponse)
async def my_applications(
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """只读取当前账户的申请历史。"""
    items, total = await list_applications(db, scope="mine", user_id=user.id, status=None, page=page, page_size=page_size)
    return FriendApplicationPrivateListResponse(items=[FriendApplicationPrivate.model_validate(item) for item in items], total=total)


@router.get("/applications/admin", response_model=FriendApplicationPrivateListResponse)
async def admin_applications(
    status: Literal["pending", "approved", "rejected"] | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin), db: AsyncSession = Depends(get_db),
):
    """管理员按状态审核完整申请。"""
    items, total = await list_applications(db, scope="admin", user_id=None, status=status, page=page, page_size=page_size)
    return FriendApplicationPrivateListResponse(items=[FriendApplicationPrivate.model_validate(item) for item in items], total=total)


@router.patch("/applications/{application_id}/review", response_model=FriendApplicationPrivate)
async def review_friend_application(
    application_id: int, data: FriendApplicationReview,
    _: User = Depends(require_admin), db: AsyncSession = Depends(get_db),
):
    """审核与生成正式友链在同一事务提交。"""
    application = await review_application(db, application_id, data.decision, data.reason)
    if application.status == "approved":
        await commit_friend_changes(db)
    else:
        await db.commit()
    return application


@router.delete("/applications/{application_id}", status_code=204)
async def remove_friend_application(
    application_id: int, _: User = Depends(require_admin), db: AsyncSession = Depends(get_db),
):
    """删除申请及其讨论，已通过记录同时移除正式友链。"""
    if not await lock_application(db, application_id):
        raise HTTPException(404, "申请不存在")
    application = await db.get(FriendApplication, application_id, populate_existing=True)
    approved = application.status == "approved"
    if not await delete_application(db, application_id):
        raise HTTPException(404, "申请不存在")
    if approved:
        await commit_friend_changes(db)
    else:
        await db.commit()


@router.put("/{friend_id}", response_model=FriendResponse)
async def edit_friend(
    friend_id: int,
    data: FriendUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新友链（管理员）"""
    friend = await update_friend(
        db, friend_id, name=data.name, bio=data.bio, avatar=data.avatar, url=data.url, sort_order=data.sort_order,
        rss_url=data.rss_url,
    )
    if not friend:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="友链不存在")
    await commit_friend_changes(db)
    return friend


@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(
    friend_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除友链（管理员）"""
    success = await delete_friend(db, friend_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="友链不存在")
    await commit_friend_changes(db)
