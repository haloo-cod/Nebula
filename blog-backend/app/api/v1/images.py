"""
图床路由 — 上传 / 列表 / 删除
"""

import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.config import settings
from app.models.image import UploadedImage
from app.models.user import User
from app.schemas.image import ImageListResponse, ImageResponse
from app.services.image import delete_file, generate_upload_path, save_upload_file

router = APIRouter(prefix="/images", tags=["图床"])


@router.post("/upload", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """上传图片到图床"""
    # 验证 MIME 类型
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file.content_type}",
        )

    # 生成路径
    relative_path, url = generate_upload_path(file.filename or "image.png")

    # 保存文件
    file_size = await save_upload_file(file, relative_path)

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
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("", response_model=ImageListResponse)
async def list_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取图床图片列表（分页）"""
    offset = (page - 1) * page_size

    total_result = await db.execute(select(func.count(UploadedImage.id)))
    total = total_result.scalar() or 0

    result = await db.execute(
        select(UploadedImage)
        .order_by(UploadedImage.created_at.desc())
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

    # 删除文件
    delete_file(image.filename)
    # 删除记录
    await db.delete(image)
    await db.commit()
