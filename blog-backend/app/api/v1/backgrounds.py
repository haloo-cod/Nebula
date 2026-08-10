"""
背景图路由 — 公开列表 + 管理员 CRUD
"""

from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
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
async def read_background_video(filename: str, request: Request):
    """公开以内联方式读取本地视频，并支持浏览器 Range 分段请求。"""
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
async def upload_background_video(file: UploadFile = File(...), _: User = Depends(require_admin)):
    suffix = Path(file.filename or "").suffix.lower()
    if VIDEO_TYPES.get(file.content_type or "") != suffix:
        raise HTTPException(status_code=400, detail="仅支持 MIME 与扩展名匹配的 MP4、WebM 或 MOV 视频")
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
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    return {"url": f"/api/v1/backgrounds/media/{target.name}", "media_type": "video", "mime_type": file.content_type or "", "file_size": size}


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
    await reorder_backgrounds(db, data.ids)
