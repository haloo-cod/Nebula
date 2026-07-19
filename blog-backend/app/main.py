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
from app.utils.security import hash_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表 + 创建默认管理员"""
    # 确保目录存在
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (settings.UPLOAD_DIR / "images").mkdir(exist_ok=True)
    (settings.UPLOAD_DIR / "books").mkdir(exist_ok=True)
    settings.CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    (settings.CONTENT_DIR / "posts").mkdir(exist_ok=True)
    (settings.CONTENT_DIR / "gallery").mkdir(exist_ok=True)
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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

# 静态文件服务（图床 + EPUB）
# 用 CORSMiddleware 包装 StaticFiles，确保 WebGL 等需要 crossOrigin 的请求能获取 CORS 头
static_app = CORSMiddleware(
    app=StaticFiles(directory=str(settings.UPLOAD_DIR)),
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.mount("/uploads", static_app, name="uploads")

# API 路由
app.include_router(v1_router)


@app.get("/")
async def root():
    return {"message": "Starlit Blog API is running"}
