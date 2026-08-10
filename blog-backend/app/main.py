"""
FastAPI 应用入口
"""

from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, select, text

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

# 仅公开图片目录；普通文件、EPUB 和 ZIP 必须通过鉴权 API 访问。
static_images = CORSMiddleware(
    app=StaticFiles(directory=str(settings.UPLOAD_DIR / "images")),
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)
# 局域网开发需要开放图片跨域时，可将 allow_origins 改为 [] 并恢复：
# allow_origin_regex=".*" if settings.CORS_ALLOW_ALL else None,
# 生产环境不要启用任意 Origin + credentials。
app.mount("/uploads/images", static_images, name="uploaded-images")
app.mount("/uploads/backgrounds", StaticFiles(directory=str(settings.UPLOAD_DIR / "backgrounds")), name="uploaded-backgrounds")

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
