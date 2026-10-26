"""
图床路由 — 上传 / 列表 / 删除
"""

import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.config import settings
from app.models.image import UploadedImage
from app.models.album import Album, AlbumPhoto
from app.models.background import Background
from app.models.book import Book
from app.models.post import Post
from app.models.carousel import CarouselSlide
from app.models.user import User
from app.schemas.image import ImageListResponse, ImageResponse
from app.services.image import delete_file, generate_upload_path, save_upload_file

router = APIRouter(prefix="/images", tags=["图床"])


@router.post("/upload", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    storage_backend: str = Query("local", pattern="^(local|r2)$"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    上传图片到图床
    - storage_backend: 'local' | 'r2'（默认 'local'）
    """
    # 验证 MIME 类型
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file.content_type}",
        )

    # R2 启用检查
    if storage_backend == "r2" and not settings.R2_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="R2 存储未启用，请检查配置",
        )

    # 生成路径
    relative_path, url = generate_upload_path(file.filename or "image.png")

    # 保存文件（根据 storage_backend 自动选择）
    file_size = await save_upload_file(file, relative_path, storage_backend)

    if file_size > settings.MAX_IMAGE_SIZE:
        delete_file(relative_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件过大，最大允许 {settings.MAX_IMAGE_SIZE // 1024 // 1024}MB",
        )

    # 尝试获取图片尺寸
    width, height = 0, 0
    try:
        await file.seek(0)
        content = await file.read()
        from PIL import Image

        img = Image.open(io.BytesIO(content))
        width, height = img.size
    except Exception:
        pass

    # 入库
    record = UploadedImage(
        filename=relative_path,
        original_name=file.filename or "image.png",
        url=url,
        file_size=file_size,
        width=width,
        height=height,
        mime_type=file.content_type or "",
        storage_backend=storage_backend,
        r2_key=relative_path if storage_backend == "r2" else None,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("", response_model=ImageListResponse)
async def list_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    storage_backend: str | None = Query(None, pattern="^(local|r2)$"),
    keyword: str | None = Query(None, max_length=300),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取图床图片列表（分页，可按存储后端过滤）"""
    offset = (page - 1) * page_size

    count_stmt = select(func.count(UploadedImage.id))
    list_stmt = select(UploadedImage)
    if storage_backend:
        count_stmt = count_stmt.where(UploadedImage.storage_backend == storage_backend)
        list_stmt = list_stmt.where(UploadedImage.storage_backend == storage_backend)
    if keyword and keyword.strip():
        term = keyword.strip()
        matches = or_(
            UploadedImage.original_name.icontains(term, autoescape=True),
            UploadedImage.filename.icontains(term, autoescape=True),
        )
        count_stmt = count_stmt.where(matches)
        list_stmt = list_stmt.where(matches)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    result = await db.execute(
        list_stmt
        .order_by(UploadedImage.created_at.desc(), UploadedImage.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = list(result.scalars().all())

    return ImageListResponse(items=items, total=total)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除图片"""
    result = await db.execute(select(UploadedImage).where(UploadedImage.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")

    # 同时保护外键引用和按 URL 保存的封面、背景来源。
    references: list[str] = []
    image_urls = {value for value in (image.url, image.filename, f"/uploads/{image.filename}") if value}
    image_urls.add(f"{settings.FRONTEND_URL.rstrip('/')}/uploads/{image.filename}")
    checks = [
        (CarouselSlide, CarouselSlide.image_id == image_id, "首页轮播"),
        (Background, or_(Background.image_id == image_id,
                         Background.media_url.in_(image_urls),
                         Background.poster_url.in_(image_urls)), "背景或视频封面"),
        (Album, Album.cover_image_id == image_id, "相册封面"),
        (AlbumPhoto, AlbumPhoto.image_id == image_id, "相册照片"),
        (Post, Post.cover_url.in_(image_urls), "文章封面"),
    ]
    for model, condition, label in checks:
        count = (await db.execute(select(func.count()).select_from(model).where(condition))).scalar() or 0
        if count:
            references.append(f"{label} {count} 处")
    book_count = (
        await db.execute(
            select(func.count()).select_from(Book).where(
                Book.cover_url.in_(image_urls)
            )
        )
    ).scalar() or 0
    if book_count:
        references.append(f"图书封面 {book_count} 处")
    if references:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"图片正在使用：{'、'.join(references)}，请先解除引用")

    # 删除文件（支持本地和 R2）
    delete_file(image.filename, storage_backend=image.storage_backend)
    # 删除记录
    await db.delete(image)
    await db.commit()
