"""
R2 迁移管理接口
"""
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import require_admin
from app.database import get_db
from app.models.image import UploadedImage
from app.models.file import UploadedFile
from app.models.background import Background
from app.models.book import Book
from app.models.user import User
from app.config import settings

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.r2_storage import R2Storage

router = APIRouter(prefix="/r2-migration", tags=["R2 迁移"])


class MigrateRequest(BaseModel):
    image_ids: list[int] = []
    file_ids: list[int] = []
    background_ids: list[int] = []
    book_ids: list[int] = []


class MigrateResponse(BaseModel):
    success_count: int
    failed_count: int
    failed_ids: list[int]
    errors: list[str]


def _require_r2() -> "R2Storage":
    """校验 R2 已启用并返回客户端，未启用/未配置统一抛 400。"""
    if not settings.R2_ENABLED:
        raise HTTPException(status_code=400, detail="R2 未启用，请检查配置")
    try:
        from app.services.r2_storage import get_r2_client
        return get_r2_client()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"R2 配置无效：{str(e)}")


@router.post("/migrate-images", response_model=MigrateResponse)
async def migrate_images_to_r2(
    req: MigrateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量迁移图片到 R2"""
    r2 = _require_r2()

    success_count = 0
    failed_count = 0
    failed_ids = []
    errors = []

    for image_id in req.image_ids:
        result = await db.execute(select(UploadedImage).where(UploadedImage.id == image_id))
        image = result.scalar_one_or_none()
        if not image:
            failed_ids.append(image_id)
            failed_count += 1
            errors.append(f"图片 {image_id} 不存在")
            continue

        # 已迁移，跳过
        if image.storage_backend == "r2":
            success_count += 1
            continue

        # 本地文件路径
        local_path = settings.UPLOAD_DIR / image.filename
        if not local_path.is_file():
            failed_ids.append(image_id)
            failed_count += 1
            errors.append(f"图片 {image_id} 本地文件不存在：{image.filename}")
            continue

        # 上传到 R2
        try:
            r2_key = image.filename
            r2.upload_local_file(r2_key, local_path, content_type=image.mime_type)

            # 更新数据库
            image.storage_backend = "r2"
            image.r2_key = r2_key
            await db.commit()
            success_count += 1
        except Exception as e:
            failed_ids.append(image_id)
            failed_count += 1
            errors.append(f"图片 {image_id} 上传失败：{str(e)}")
            await db.rollback()

    return MigrateResponse(
        success_count=success_count,
        failed_count=failed_count,
        failed_ids=failed_ids,
        errors=errors,
    )


@router.post("/migrate-files", response_model=MigrateResponse)
async def migrate_files_to_r2(
    req: MigrateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量迁移通用文件到 R2"""
    r2 = _require_r2()

    success_count = 0
    failed_count = 0
    failed_ids = []
    errors = []

    for file_id in req.file_ids:
        result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
        file = result.scalar_one_or_none()
        if not file:
            failed_ids.append(file_id)
            failed_count += 1
            errors.append(f"文件 {file_id} 不存在")
            continue

        if file.storage_backend == "r2":
            success_count += 1
            continue

        local_path = settings.UPLOAD_DIR / file.filename
        if not local_path.is_file():
            failed_ids.append(file_id)
            failed_count += 1
            errors.append(f"文件 {file_id} 本地文件不存在")
            continue

        try:
            r2_key = file.filename
            r2.upload_local_file(r2_key, local_path, content_type=file.mime_type)

            file.storage_backend = "r2"
            file.r2_key = r2_key
            await db.commit()
            success_count += 1
        except Exception as e:
            failed_ids.append(file_id)
            failed_count += 1
            errors.append(f"文件 {file_id} 上传失败：{str(e)}")
            await db.rollback()

    return MigrateResponse(
        success_count=success_count,
        failed_count=failed_count,
        failed_ids=failed_ids,
        errors=errors,
    )


def _background_local_name(background: Background) -> str | None:
    """从背景记录提取自有视频的本地相对路径（backgrounds/xxx.mp4）。

    仅识别本站生成的两种 URL 格式；外链或文件管理引用（/api/v1/files/...）
    不属于背景表自身管理的文件，返回 None。
    """
    url = background.media_url
    for prefix in ("/uploads/backgrounds/", "/api/v1/backgrounds/media/"):
        if url.startswith(prefix):
            name = url.removeprefix(prefix)
            if name and "/" not in name and "\\" not in name:
                return f"backgrounds/{name}"
    return None


@router.post("/migrate-backgrounds", response_model=MigrateResponse)
async def migrate_backgrounds_to_r2(
    req: MigrateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量迁移背景自有视频到 R2。

    图片背景与引用文件管理（/api/v1/files/{id}/media）的视频不在迁移范围：
    前者随图床图片迁移，后者随通用文件迁移。
    """
    r2 = _require_r2()

    success_count = 0
    failed_count = 0
    failed_ids = []
    errors = []

    for bg_id in req.background_ids:
        result = await db.execute(select(Background).where(Background.id == bg_id))
        background = result.scalar_one_or_none()
        if not background:
            failed_ids.append(bg_id)
            failed_count += 1
            errors.append(f"背景 {bg_id} 不存在")
            continue

        if background.media_type != "video":
            failed_ids.append(bg_id)
            failed_count += 1
            errors.append(f"背景 {bg_id} 不是视频背景，请通过图片迁移处理")
            continue

        if background.storage_backend == "r2":
            success_count += 1
            continue

        relative = _background_local_name(background)
        if relative is None:
            failed_ids.append(bg_id)
            failed_count += 1
            errors.append(f"背景 {bg_id} 引用的是外部/文件管理视频，请通过对应来源迁移")
            continue

        local_path = settings.UPLOAD_DIR / relative
        if not local_path.is_file():
            failed_ids.append(bg_id)
            failed_count += 1
            errors.append(f"背景 {bg_id} 本地文件不存在：{relative}")
            continue

        try:
            r2.upload_local_file(relative, local_path, content_type=background.mime_type or None)
            background.storage_backend = "r2"
            background.r2_key = relative
            await db.commit()
            success_count += 1
        except Exception as e:
            failed_ids.append(bg_id)
            failed_count += 1
            errors.append(f"背景 {bg_id} 上传失败：{str(e)}")
            await db.rollback()

    return MigrateResponse(
        success_count=success_count,
        failed_count=failed_count,
        failed_ids=failed_ids,
        errors=errors,
    )


@router.post("/migrate-books", response_model=MigrateResponse)
async def migrate_books_to_r2(
    req: MigrateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量迁移图书 EPUB 到 R2。

    本地保留副本：epub.js 阅读器需要服务端按 ZIP 内部路径随机读取资源，
    封面提取/候选图等管理操作也依赖本地文件。R2 作为权威存储 + 公网分发入口。
    """
    r2 = _require_r2()

    success_count = 0
    failed_count = 0
    failed_ids = []
    errors = []

    for book_id in req.book_ids:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        if not book:
            failed_ids.append(book_id)
            failed_count += 1
            errors.append(f"图书 {book_id} 不存在")
            continue

        if book.storage_backend == "r2":
            success_count += 1
            continue

        local_path = settings.UPLOAD_DIR / "books" / f"{book.slug}.epub"
        if not local_path.is_file():
            failed_ids.append(book_id)
            failed_count += 1
            errors.append(f"图书 {book_id} 本地文件不存在：books/{book.slug}.epub")
            continue

        r2_key = f"books/{book.slug}.epub"
        try:
            r2.upload_local_file(r2_key, local_path, content_type="application/epub+zip")
            book.storage_backend = "r2"
            book.r2_key = r2_key
            await db.commit()
            success_count += 1
        except Exception as e:
            failed_ids.append(book_id)
            failed_count += 1
            errors.append(f"图书 {book_id} 上传失败：{str(e)}")
            await db.rollback()

    return MigrateResponse(
        success_count=success_count,
        failed_count=failed_count,
        failed_ids=failed_ids,
        errors=errors,
    )


@router.get("/migration-status")
async def get_migration_status(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取迁移状态统计"""
    # 图片统计
    total_images = (await db.execute(select(func.count(UploadedImage.id)))).scalar() or 0
    migrated_images = (
        await db.execute(
            select(func.count(UploadedImage.id)).where(UploadedImage.storage_backend == "r2")
        )
    ).scalar() or 0

    # 文件统计
    total_files = (await db.execute(select(func.count(UploadedFile.id)))).scalar() or 0
    migrated_files = (
        await db.execute(
            select(func.count(UploadedFile.id)).where(UploadedFile.storage_backend == "r2")
        )
    ).scalar() or 0

    # 背景统计（仅统计背景表自有的视频文件；图片背景随图床统计，
    # 引用文件管理的视频随通用文件统计，避免重复计数）
    # 口径与 _background_local_name 守卫一致：仅本站两种 URL 格式算自有视频，
    # /api/v1/files/... 引用型与外链均不计入（前者随通用文件迁移，后者无法迁移）
    own_video_filter = (Background.media_type == "video") & (
        Background.media_url.startswith("/uploads/backgrounds/")
        | Background.media_url.startswith("/api/v1/backgrounds/media/")
    )
    total_backgrounds = (
        await db.execute(select(func.count(Background.id)).where(own_video_filter))
    ).scalar() or 0
    migrated_backgrounds = (
        await db.execute(
            select(func.count(Background.id)).where(
                own_video_filter, Background.storage_backend == "r2"
            )
        )
    ).scalar() or 0

    # 书籍统计
    total_books = (await db.execute(select(func.count(Book.id)))).scalar() or 0
    migrated_books = (
        await db.execute(
            select(func.count(Book.id)).where(Book.storage_backend == "r2")
        )
    ).scalar() or 0

    return {
        "r2_enabled": settings.R2_ENABLED,
        "images": {
            "total": total_images,
            "migrated": migrated_images,
            "pending": total_images - migrated_images,
        },
        "files": {
            "total": total_files,
            "migrated": migrated_files,
            "pending": total_files - migrated_files,
        },
        "backgrounds": {
            "total": total_backgrounds,
            "migrated": migrated_backgrounds,
            "pending": total_backgrounds - migrated_backgrounds,
        },
        "books": {
            "total": total_books,
            "migrated": migrated_books,
            "pending": total_books - migrated_books,
        },
    }


@router.get("/storage-config")
async def get_storage_config(
    _: User = Depends(require_admin),
):
    """获取当前存储配置"""
    return {
        "r2_enabled": settings.R2_ENABLED,
        "r2_configured": bool(
            settings.R2_ACCOUNT_ID
            and settings.R2_ACCESS_KEY_ID
            and settings.R2_SECRET_ACCESS_KEY
            and settings.R2_BUCKET_NAME
        ),
        "default_storage": "r2" if settings.R2_ENABLED else "local",
    }


class PresignRequest(BaseModel):
    """预签名直传请求"""

    filename: str  # 含扩展名的原始文件名，仅用于推断目录与扩展名
    content_type: str = "application/octet-stream"
    directory: str = "images"  # R2 键前缀目录，如 images / files


class PresignResponse(BaseModel):
    """预签名直传响应"""

    upload_url: str  # 预签名 PUT URL，浏览器直传 R2
    r2_key: str  # 上传成功后回填记录用的对象键
    url: str  # 记录的访问 URL（/uploads/{r2_key}）
    cache_control: str  # PUT 时必须回传的 Cache-Control 头值（已参与签名）
    storage_backend: str = "r2"


@router.post("/presign-upload", response_model=PresignResponse)
async def presign_upload(
    req: PresignRequest,
    _: User = Depends(require_admin),
):
    """生成预签名 PUT URL，供浏览器直传 R2（不经过服务器）。

    仅支持通用文件（files/）与图床图片（images/）两类。EPUB 与背景视频
    需要服务端本地副本（epub.js 随机读取 / 视频转码探测），仍走服务器中转。
    上传完成后调用方需要自行创建数据库记录（storage_backend='r2'）。
    需要 R2 桶 CORS 允许来自站点源的 PUT 请求。
    """
    if not settings.R2_ENABLED:
        raise HTTPException(status_code=400, detail="R2 未启用，请检查配置")

    allowed_dirs = {"images", "files"}
    if req.directory not in allowed_dirs:
        raise HTTPException(status_code=400, detail=f"目录必须是 {sorted(allowed_dirs)} 之一")

    suffix = Path(req.filename).suffix.lower()
    if not suffix or len(suffix) > 10 or not re.fullmatch(r"\.[a-z0-9]+", suffix):
        raise HTTPException(status_code=400, detail="文件名必须带合法扩展名")

    if req.directory == "images":
        r2_key = _generate_image_key(req.filename)
    else:
        r2_key = f"files/{uuid4().hex}{suffix}"
    r2 = _require_r2()
    from app.services.r2_storage import R2_CACHE_CONTROL

    try:
        upload_url = r2.presign_put(
            r2_key, content_type=req.content_type, cache_control=R2_CACHE_CONTROL
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"生成预签名 URL 失败：{str(e)}")

    return PresignResponse(
        upload_url=upload_url,
        r2_key=r2_key,
        url=f"/uploads/{r2_key}",
        cache_control=R2_CACHE_CONTROL,
    )


def _generate_image_key(original_name: str) -> str:
    """按图床规则生成 images/{year}/{month}/{uuid}_{name} 键名。"""
    now = datetime.now()
    suffix = Path(original_name).suffix.lower()
    unique_name = f"{uuid4().hex[:12]}_{Path(original_name).stem}{suffix}"
    return f"images/{now.year}/{now.month:02d}/{unique_name}"


class RegisterUploadRequest(BaseModel):
    """预签名直传完成后登记数据库记录"""

    directory: str  # 'images' | 'files'
    r2_key: str  # presign 响应返回的对象键
    original_name: str
    mime_type: str = "application/octet-stream"
    file_size: int = 0
    width: int = 0
    height: int = 0


@router.post("/register-upload", status_code=status.HTTP_201_CREATED)
async def register_upload(
    req: RegisterUploadRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """预签名直传完成后登记记录，并校验对象确实已在 R2 上。"""
    if req.directory not in ("images", "files"):
        raise HTTPException(status_code=400, detail="directory 必须是 images 或 files")
    if req.r2_key.split("/", 1)[0] != req.directory:
        raise HTTPException(status_code=400, detail="r2_key 目录与 directory 不匹配")

    r2 = _require_r2()
    if not r2.file_exists(req.r2_key):
        raise HTTPException(status_code=400, detail="对象尚未上传到 R2，请先完成直传")

    if req.directory == "images":
        record = UploadedImage(
            filename=req.r2_key,
            original_name=req.original_name,
            url=f"/uploads/{req.r2_key}",
            file_size=req.file_size,
            width=req.width,
            height=req.height,
            mime_type=req.mime_type,
            storage_backend="r2",
            r2_key=req.r2_key,
        )
    else:
        record = UploadedFile(
            filename=req.r2_key,
            original_name=req.original_name,
            file_size=req.file_size,
            mime_type=req.mime_type,
            storage_backend="r2",
            r2_key=req.r2_key,
        )
    db.add(record)
    if req.directory == "files":
        # 文件记录的 URL 依赖自增 id，先 flush 再回填
        await db.flush()
        record.url = f"/api/v1/files/{record.id}/download"
    await db.commit()
    await db.refresh(record)
    return {
        "id": record.id,
        "filename": record.filename,
        "original_name": record.original_name,
        "url": record.url,
        "file_size": record.file_size,
        "mime_type": record.mime_type,
    }


@router.post("/backfill-cache", response_model=MigrateResponse)
async def backfill_cache_metadata(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """为全部已迁移（storage_backend='r2'）的对象补写 Cache-Control 元数据。

    早期迁移/上传的对象未写缓存头，浏览器无法缓存（每次刷新全量重拉）。
    通过服务端自复制（copy_source=自身 + REPLACE 元数据）逐个补写，
    对象键名与内容不变。幂等：重复执行只是再次复制。
    """
    r2 = _require_r2()

    # (表, 过滤条件, 取 r2_key 的列) — 与 migration-status 的统计口径一致
    queries = [
        (UploadedImage, UploadedImage.storage_backend == "r2", UploadedImage.r2_key),
        (UploadedFile, UploadedFile.storage_backend == "r2", UploadedFile.r2_key),
        (Background, Background.storage_backend == "r2", Background.r2_key),
        (Book, Book.storage_backend == "r2", Book.r2_key),
    ]

    success_count = 0
    failed_count = 0
    failed_ids: list[int] = []
    errors: list[str] = []

    for model, where_clause, key_column in queries:
        result = await db.execute(
            select(model.id, key_column).where(
                where_clause, key_column.isnot(None), key_column != ""
            )
        )
        rows = result.all()
        for row_id, r2_key in rows:
            if not r2_key:
                continue
            try:
                if r2.copy_cache_metadata(r2_key):
                    success_count += 1
                else:
                    failed_count += 1
                    failed_ids.append(row_id)
                    errors.append(f"{model.__name__} {row_id} 对象不存在：{r2_key}")
            except Exception as e:
                failed_count += 1
                failed_ids.append(row_id)
                errors.append(f"{model.__name__} {row_id} 补写失败：{str(e)}")

    return MigrateResponse(
        success_count=success_count,
        failed_count=failed_count,
        failed_ids=failed_ids,
        errors=errors,
    )
