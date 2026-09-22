"""
背景图路由 — 公开列表 + 管理员 CRUD
"""

from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.background import Background
from app.models.user import User
from app.schemas.background import (
    BackgroundCreate,
    BackgroundListResponse,
    BackgroundReorderRequest,
    BackgroundResponse,
)
from app.services.background import (
    create_background,
    delete_background,
    list_backgrounds,
    reorder_backgrounds,
)
from app.config import settings

router = APIRouter(prefix="/backgrounds", tags=["背景图"])

VIDEO_TYPES = {"video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov"}
# 限制视频大小（可按需调整）
MAX_VIDEO_SIZE = 50 * 1024 * 1024


def _safe_video_path(filename: str) -> Path:
    path = (settings.UPLOAD_DIR / "backgrounds" / filename).resolve()
    root = (settings.UPLOAD_DIR / "backgrounds").resolve()
    if path.parent != root or path.suffix.lower() not in VIDEO_TYPES.values() or not path.is_file():
        raise HTTPException(status_code=404, detail="视频不存在")
    return path


@router.get("/media/{filename:path}")
async def read_background_video(
    filename: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """公开以内联方式读取视频，并支持浏览器 Range 分段请求。

    存储路由：记录为 r2 时优先走 R2（配置公开域名则 307 重定向让浏览器
    直连 CDN，否则后端流式代理），本地文件始终作为兜底。
    """
    if settings.R2_ENABLED:
        result = await db.execute(
            select(Background).where(Background.media_url == f"/api/v1/backgrounds/media/{filename}")
        )
        background = result.scalar_one_or_none()
        if background and background.storage_backend == "r2" and background.r2_key:
            from app.services.r2_storage import get_r2_client

            r2 = get_r2_client()
            if settings.R2_PUBLIC_DOMAIN:
                url = r2.get_public_url(background.r2_key)
                # 透传查询串，避免 CORS / no-cors 请求收敛到同一缓存键（同 main.py）
                if request.url.query:
                    url = f"{url}?{request.url.query}"
                return RedirectResponse(url, status_code=307)
            media_type = background.mime_type or "video/mp4"
            return StreamingResponse(r2.download_stream(background.r2_key), media_type=media_type)

    path = _safe_video_path(filename)
    size = path.stat().st_size
    start, end = 0, size - 1
    range_header = request.headers.get("range")
    status_code = status.HTTP_200_OK
    if range_header:
        try:
            unit, value = range_header.split("=", 1)
            if unit.strip().lower() != "bytes":
                raise ValueError
            first, last = value.split("-", 1)
            if first:
                start = int(first)
                end = int(last) if last else size - 1
            else:
                length = int(last)
                start = max(size - length, 0)
            if start < 0 or start >= size or end < start:
                raise ValueError
            end = min(end, size - 1)
            status_code = status.HTTP_206_PARTIAL_CONTENT
        except (ValueError, TypeError):
            return StreamingResponse(iter(()), status_code=416, headers={"Content-Range": f"bytes */{size}"})
    length = end - start + 1

    def iterator():
        with path.open("rb") as stream:
            stream.seek(start)
            remaining = length
            while remaining:
                chunk = stream.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    mime = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime"}[path.suffix.lower()]
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(length),
        "Content-Type": mime,
        "Content-Disposition": "inline",
        "Cache-Control": "public, max-age=86400",
    }
    if status_code == status.HTTP_206_PARTIAL_CONTENT:
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    return StreamingResponse(iterator(), status_code=status_code, headers=headers, media_type=mime)

@router.post("/video-upload")
async def upload_background_video(
    storage_backend: str = Query("local", pattern="^(local|r2)$"),
    file: UploadFile = File(...),
    _: User = Depends(require_admin),
):
    """上传背景视频。storage_backend=r2 时写盘后同步转传 R2（本地副本保留作兜底）。"""
    suffix = Path(file.filename or "").suffix.lower()
    if VIDEO_TYPES.get(file.content_type or "") != suffix:
        raise HTTPException(status_code=400, detail="仅支持 MIME 与扩展名匹配的 MP4、WebM 或 MOV 视频")
    if storage_backend == "r2" and not settings.R2_ENABLED:
        raise HTTPException(status_code=400, detail="R2 未启用，无法使用 r2 存储")
    relative = Path("backgrounds") / f"{uuid4().hex}{suffix}"
    target = settings.UPLOAD_DIR / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    try:
        with target.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_VIDEO_SIZE:
                    raise HTTPException(status_code=413, detail=f"视频不能超过 {MAX_VIDEO_SIZE // (1024 * 1024)}MB")
                output.write(chunk)
        if storage_backend == "r2":
            from app.services.r2_storage import get_r2_client

            get_r2_client().upload_local_file(
                str(relative), target, content_type=file.content_type
            )
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    return {
        "url": f"/api/v1/backgrounds/media/{target.name}",
        "media_type": "video",
        "mime_type": file.content_type or "",
        "file_size": size,
        "storage_backend": storage_backend,
    }


@router.get("", response_model=BackgroundListResponse)
async def get_backgrounds(
    theme: str | None = Query(None, description="主题过滤: dark / light"),
    device: str | None = Query(None, description="设备过滤: desktop / mobile"),
    db: AsyncSession = Depends(get_db),
):
    """获取背景图列表（公开接口，可按 theme/device 筛选）"""
    items = await list_backgrounds(db, theme=theme, device=device)
    return BackgroundListResponse(items=items, total=len(items))


@router.post("", response_model=BackgroundResponse, status_code=status.HTTP_201_CREATED)
async def add_background(
    data: BackgroundCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """创建背景图记录（管理员）"""
    try:
        result = await create_background(
            db,
            image_id=data.image_id,
            theme=data.theme,
            device=data.device,
            sort_order=data.sort_order,
            media_type=data.media_type,
            media_url=data.media_url,
            poster_url=data.poster_url,
            mime_type=data.mime_type,
            file_size=data.file_size,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return result


@router.delete("/{bg_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_background(
    bg_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除背景图记录（管理员，不删除图片文件）"""
    success = await delete_background(db, bg_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="背景图不存在")


@router.put("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder(
    data: BackgroundReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量调整背景图排序（管理员）"""
    try:
        await reorder_backgrounds(db, data.ids, data.theme, data.device)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
