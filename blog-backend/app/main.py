"""
FastAPI 应用入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api.v1.router import router as v1_router
from app.config import settings
from app.database import engine, AsyncSessionLocal
from app.middleware.cors import setup_cors
from app.models import Base
from app.models.user import User
from app.services.schema_migration import migrate_existing_schema
from app.utils.security import hash_password
from app.services.book_download import cleanup_expired_book_archives


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表 + 创建默认管理员"""
    # 确保目录存在
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (settings.UPLOAD_DIR / "images").mkdir(exist_ok=True)
    (settings.UPLOAD_DIR / "books").mkdir(exist_ok=True)
    (settings.UPLOAD_DIR / "files").mkdir(exist_ok=True)
    settings.BOOK_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_expired_book_archives()
    settings.CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    (settings.CONTENT_DIR / "posts").mkdir(exist_ok=True)
    (settings.CONTENT_DIR / "gallery").mkdir(exist_ok=True)
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await migrate_existing_schema(engine)

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
app.mount("/uploads/images", static_images, name="uploaded-images")

# API 路由
app.include_router(v1_router)


@app.get("/")
async def root():
    return {"message": "Starlit Blog API is running"}
