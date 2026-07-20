"""
通用文件路由 — 管理员上传/列表/删除，公开强制下载
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse as DownloadResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.database import get_db
from app.models.file import UploadedFile
from app.models.user import User
from app.schemas.file import FileListResponse, FileResponse
from app.services.file import delete_file, generate_file_path, get_file_path, save_file
from app.services.analytics import get_client_ip, hash_ip, utc_now
from app.models.analytics import AnalyticsEvent

router = APIRouter(prefix="/files", tags=["文件"])


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """上传任意类型文件，不设置应用层文件大小限制。"""

    original_name = file.filename or "download"
    relative_path = generate_file_path(original_name)
    file_size = await save_file(file, relative_path)

    record = UploadedFile(
        filename=relative_path,
        original_name=original_name,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
    )
    db.add(record)
    try:
        await db.flush()
        record.url = f"/api/v1/files/{record.id}/download"
        await db.commit()
        await db.refresh(record)
    except Exception:
        await db.rollback()
        delete_file(relative_path)
        raise
    finally:
        await file.close()

    return record


@router.get("", response_model=FileListResponse)
async def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """分页获取已上传的通用文件。"""

    total_result = await db.execute(select(func.count(UploadedFile.id)))
    total = total_result.scalar() or 0
    result = await db.execute(
        select(UploadedFile)
        .order_by(UploadedFile.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return FileListResponse(items=list(result.scalars().all()), total=total)


@router.head(
    "/{file_id}/download",
    response_class=DownloadResponse,
    include_in_schema=False,
)
@router.get("/{file_id}/download", response_class=DownloadResponse)
async def download_file(
    file_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """登录用户下载藏宝阁资源，并记录访问行为。"""

    result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    path = get_file_path(record.filename)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件已丢失")

    ip_address = get_client_ip(request)
    ip_hash = hash_ip(ip_address)
    since = utc_now() - timedelta(hours=1)
    recent = await db.execute(
        select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.event_type == "file_download",
            AnalyticsEvent.ip_hash == ip_hash,
            AnalyticsEvent.occurred_at >= since,
        )
    )
    if int(recent.scalar() or 0) >= 30:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="下载过于频繁，请稍后再试")

    db.add(
        AnalyticsEvent(
            event_type="file_download",
            path=f"/api/v1/files/{file_id}/download",
            title=record.original_name,
            user_agent=request.headers.get("user-agent", "")[:1000],
            ip_address=ip_address,
            ip_hash=ip_hash,
            user_id=user.id,
            occurred_at=utc_now(),
        )
    )
    await db.commit()

    return DownloadResponse(
        path=path,
        filename=record.original_name,
        media_type=record.mime_type or "application/octet-stream",
        content_disposition_type="attachment",
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除通用文件记录和磁盘文件。"""

    result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    delete_file(record.filename)
    await db.delete(record)
    await db.commit()
