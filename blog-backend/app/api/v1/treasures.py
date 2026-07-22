"""
藏宝阁路由 — 公开列表 + 管理员 CRUD
"""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.database import get_db
from app.models.book_download import BookDownloadJob
from app.models.treasure import Treasure
from app.models.user import User
from app.schemas.treasure import (
    TreasureCreate,
    TreasureListResponse,
    TreasureResponse,
    TreasureUpdate,
)
from app.services.treasure import (
    create_treasure,
    delete_treasure,
    get_categories,
    list_treasures,
    update_treasure,
)
from app.services.slug import unique_slug

router = APIRouter(prefix="/treasures", tags=["藏宝阁"])


def _archive_id(download_file: str) -> int | None:
    """从藏宝阁归档下载地址提取任务 ID。"""
    if "/api/v1/treasures/archive/" in download_file and download_file.endswith("/download"):
        value = download_file.split("/archive/", 1)[1].removesuffix("/download")
    elif "?archive=" in download_file:
        value = download_file.rsplit("?archive=", 1)[-1]
    else:
        return None
    return int(value) if value.isdigit() else None


async def _treasure_response(db: AsyncSession, treasure: Treasure) -> TreasureResponse:
    """补充藏宝条目关联归档的状态和到期时间。"""
    response = TreasureResponse.model_validate(treasure)
    archive_id = _archive_id(treasure.download_file)
    if archive_id is None:
        return response
    job = await db.get(BookDownloadJob, archive_id)
    if not job:
        return response.model_copy(update={"archive_id": archive_id, "archive_status": "missing"})
    expires_at = job.expires_at
    archive_status = job.status
    if expires_at and expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        archive_status = "expired"
    return response.model_copy(
        update={
            "archive_id": archive_id,
            "archive_status": archive_status,
            "archive_expires_at": expires_at,
        }
    )


@router.get("", response_model=TreasureListResponse)
async def get_treasures(
    category: str | None = Query(None, description="分类筛选"),
    db: AsyncSession = Depends(get_db),
):
    """获取藏宝列表（公开接口，可按分类筛选）"""
    items = await list_treasures(db, category=category)
    return TreasureListResponse(
        items=[await _treasure_response(db, item) for item in items],
        total=len(items),
    )


@router.get("/categories", response_model=list[str])
async def get_treasure_categories(db: AsyncSession = Depends(get_db)):
    """获取所有分类列表（公开接口）"""
    return await get_categories(db)


@router.get("/archive/{archive}/download", response_class=FileResponse)
async def download_treasure_archive(
    archive: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """下载已挂载到藏宝阁的图书归档。"""
    if archive < 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="藏宝归档不存在")
    result = await db.execute(select(Treasure))
    is_mounted = any(_archive_id(item.download_file) == archive for item in result.scalars().all())
    if not is_mounted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书归档未挂载到藏宝阁")
    return await _send_treasure_archive(db, archive)


async def _send_treasure_archive(db: AsyncSession, archive: int) -> FileResponse:
    """校验归档状态并返回 ZIP 文件。"""
    job = await db.get(BookDownloadJob, archive)
    expires_at = job.expires_at if job else None
    if not job or job.status not in {"completed", "expired"} or not job.output_path or (
        expires_at and expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书归档不可用")
    path = Path(job.output_path)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书归档文件不存在")
    filename = f"{job.archive_name.removesuffix('.zip')}.zip"
    return FileResponse(path, filename=filename, media_type="application/zip")


@router.get("/{slug:path}/download", response_class=FileResponse)
async def download_treasure(
    slug: str,
    archive: int = Query(..., ge=1, description="图书归档任务 ID"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """下载藏宝阁公开挂载的图书归档。"""
    treasure_result = await db.execute(select(Treasure).where(Treasure.slug == slug)) if slug else None
    treasure = treasure_result.scalar_one_or_none() if treasure_result else None
    # 兼容旧版空 Slug 地址，同时仍要求该归档确实挂载在某个藏宝条目上。
    if not treasure:
        treasure_result = await db.execute(
            select(Treasure).where(
                Treasure.download_file == f"/api/v1/treasures//download?archive={archive}"
            )
        )
        treasure = treasure_result.scalar_one_or_none()
    if not treasure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="藏宝条目不存在")

    expected_url = f"/api/v1/treasures/{treasure.slug}/download?archive={archive}"
    canonical_url = f"/api/v1/treasures/archive/{archive}/download"
    legacy_url = f"/api/v1/treasures//download?archive={archive}"
    if treasure.download_file not in {expected_url, canonical_url, legacy_url}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该资源不是图书归档")

    return await _send_treasure_archive(db, archive)


@router.post("", response_model=TreasureResponse, status_code=status.HTTP_201_CREATED)
async def add_treasure(
    data: TreasureCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """创建藏宝条目（管理员）"""
    treasure = await create_treasure(
        db,
        slug=await unique_slug(db, Treasure, data.slug or data.title, "treasure"),
        title=data.title,
        description=data.description,
        category=data.category,
        icon=data.icon,
        url=data.url,
        download_file=data.download_file,
        tags=data.tags,
        sort_order=data.sort_order,
    )
    return treasure


@router.put("/{treasure_id}", response_model=TreasureResponse)
async def edit_treasure(
    treasure_id: int,
    data: TreasureUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新藏宝条目（管理员）"""
    treasure = await update_treasure(
        db,
        treasure_id,
        title=data.title,
        description=data.description,
        category=data.category,
        icon=data.icon,
        url=data.url,
        download_file=data.download_file,
        tags=data.tags,
        sort_order=data.sort_order,
    )
    if not treasure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="藏宝条目不存在")
    return treasure


@router.delete("/{treasure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_treasure(
    treasure_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除藏宝条目（管理员）"""
    success = await delete_treasure(db, treasure_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="藏宝条目不存在")
