"""
FastAPI 应用入口
"""

from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import delete, select, text, or_

from app.api.v1.router import router as v1_router
from app.config import settings, validate_production_settings
from app.database import engine, AsyncSessionLocal
from app.middleware.cors import setup_cors
from app.models import Base
from app.models.user import User
from app.models.analytics import AnalyticsEvent
from app.models.rate_limit import RateLimitHit
from app.services.schema_migration import migrate_existing_schema
from app.utils.security import hash_password
from app.services.book_download import cleanup_expired_book_archives
from app.services.post_download import cleanup_expired_post_archives
from app.services.analytics import utc_now

for _upload_subdir in ("images", "books", "files", "backgrounds"):
    (settings.UPLOAD_DIR / _upload_subdir).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表 + 创建默认管理员"""
    validate_production_settings()
    # 确保目录存在
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (settings.UPLOAD_DIR / "images").mkdir(exist_ok=True)
    (settings.UPLOAD_DIR / "books").mkdir(exist_ok=True)
    (settings.UPLOAD_DIR / "files").mkdir(exist_ok=True)
    (settings.UPLOAD_DIR / "backgrounds").mkdir(exist_ok=True)
    settings.BOOK_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    settings.CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    (settings.CONTENT_DIR / "posts").mkdir(exist_ok=True)
    (settings.CONTENT_DIR / "gallery").mkdir(exist_ok=True)
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.DATABASE_URL.startswith("sqlite"):
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA busy_timeout=5000"))
    await migrate_existing_schema(engine)
    # 先完成旧数据库字段迁移，再查询归档任务进行过期清理。
    await cleanup_expired_book_archives()
    await cleanup_expired_post_archives()

    # 启动时清理过期访问明细，避免原始 IP 长期保留。
    async with AsyncSessionLocal() as cleanup_session:
        cutoff = utc_now() - timedelta(days=settings.ANALYTICS_IP_RETENTION_DAYS)
        await cleanup_session.execute(delete(AnalyticsEvent).where(AnalyticsEvent.occurred_at < cutoff))
        await cleanup_session.execute(
            delete(RateLimitHit).where(RateLimitHit.occurred_at < utc_now() - timedelta(days=2))
        )
        await cleanup_session.commit()

    # 初始化管理员账户（如果不存在）
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.username == settings.ADMIN_USERNAME)
        )
        if not result.scalar_one_or_none():
            admin = User(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                is_admin=True,
            )
            session.add(admin)
            await session.commit()

    yield

    # 关闭引擎
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# 中间件
setup_cors(app)

# 统一文件分发路由（支持本地和 R2 动态判断）
@app.get("/uploads/{file_path:path}")
async def serve_upload_file(
    request: Request,
    file_path: str,
    db: AsyncSessionLocal = Depends(lambda: AsyncSessionLocal()),
):
    """
    统一文件分发：根据数据库 storage_backend 动态路由
    - local → 本地磁盘
    - r2 + 自定义域名 → 302 重定向到 R2 公开域名（浏览器直连 Cloudflare，不占服务器带宽）
    - r2 无自定义域名 → 后端流式代理
    """

    def _r2_redirect(r2_key: str):
        """配置了公开域名时直接重定向，让浏览器直连 R2/CDN。"""
        from fastapi.responses import RedirectResponse

        url = get_r2_client().get_public_url(r2_key)
        # 透传查询串（如液态玻璃的 _cors=2）：丢弃会让 CORS / no-cors 两类请求
        # 收敛到同一 R2 URL，无 ACAO 的缓存响应会被 CORS fetch 复用而跨域失败。
        if request.url.query:
            url = f"{url}?{request.url.query}"
        return RedirectResponse(url, status_code=307)

    from app.models.image import UploadedImage
    from app.models.file import UploadedFile
    from app.models.background import Background

    try:
        # 1. 尝试从 UploadedImage 查找
        result = await db.execute(
            select(UploadedImage).where(
                or_(
                    UploadedImage.filename == file_path,
                    UploadedImage.filename == f"images/{file_path}",
                )
            )
        )
        image = result.scalar_one_or_none()
        if image:
            if image.storage_backend == "r2" and image.r2_key and settings.R2_ENABLED:
                from app.services.r2_storage import get_r2_client

                if settings.R2_PUBLIC_DOMAIN:
                    return _r2_redirect(image.r2_key)
                r2 = get_r2_client()
                stream = r2.download_stream(image.r2_key)
                return StreamingResponse(stream, media_type=image.mime_type or "application/octet-stream")
            else:
                local_path = settings.UPLOAD_DIR / image.filename
                if not local_path.is_file():
                    raise HTTPException(status_code=404, detail="文件不存在")
                return FileResponse(local_path, media_type=image.mime_type)

        # 2. 尝试从 UploadedFile 查找
        result = await db.execute(
            select(UploadedFile).where(
                or_(
                    UploadedFile.filename == file_path,
                    UploadedFile.filename == f"files/{file_path}",
                )
            )
        )
        file_record = result.scalar_one_or_none()
        if file_record:
            if file_record.storage_backend == "r2" and file_record.r2_key and settings.R2_ENABLED:
                from app.services.r2_storage import get_r2_client

                if settings.R2_PUBLIC_DOMAIN:
                    return _r2_redirect(file_record.r2_key)
                r2 = get_r2_client()
                stream = r2.download_stream(file_record.r2_key)
                return StreamingResponse(stream, media_type=file_record.mime_type or "application/octet-stream")
            else:
                local_path = settings.UPLOAD_DIR / file_record.filename
                if not local_path.is_file():
                    raise HTTPException(status_code=404, detail="文件不存在")
                return FileResponse(local_path, media_type=file_record.mime_type)

        # 3. 尝试从 Background 查找（视频）
        if file_path.startswith("backgrounds/"):
            result = await db.execute(
                select(Background).where(Background.media_url == f"/uploads/{file_path}")
            )
            background = result.scalar_one_or_none()
            if background:
                if background.storage_backend == "r2" and background.r2_key and settings.R2_ENABLED:
                    from app.services.r2_storage import get_r2_client

                    if settings.R2_PUBLIC_DOMAIN:
                        return _r2_redirect(background.r2_key)
                    r2 = get_r2_client()
                    stream = r2.download_stream(background.r2_key)
                    return StreamingResponse(stream, media_type=background.mime_type or "video/mp4")
                else:
                    local_path = settings.UPLOAD_DIR / file_path
                    if not local_path.is_file():
                        raise HTTPException(status_code=404, detail="文件不存在")
                    return FileResponse(local_path, media_type=background.mime_type or "video/mp4")

        # 4. 兜底：直接尝试本地文件
        local_path = settings.UPLOAD_DIR / file_path
        if local_path.is_file():
            return FileResponse(local_path)

        raise HTTPException(status_code=404, detail="文件不存在")
    finally:
        await db.close()


# 仅图片目录保留旧的静态挂载（作为降级方案）
# 生产环境可逐步移除，全部走动态路由

# API 路由
app.include_router(v1_router)


@app.get("/")
async def root():
    return {"message": "Starlit Blog API is running"}


@app.get("/health")
async def health():
    """供 Nginx、systemd 和监控检查应用进程是否可用。"""
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
