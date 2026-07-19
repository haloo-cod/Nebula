"""
全局配置 — 通过环境变量 / .env 文件加载
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ===== 应用 =====
    APP_NAME: str = "Starlit Blog API"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # ===== 数据库 =====
    DATABASE_URL: str = "sqlite+aiosqlite:///./blog.db"

    # ===== 文件存储 =====
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    CONTENT_DIR: Path = BASE_DIR / "content"
    DATA_DIR: Path = BASE_DIR / "data"

    # 图片上传限制
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_IMAGE_TYPES: list[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/svg+xml",
    ]

    # ===== CORS =====
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # ===== 管理员初始账户 =====
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"


settings = Settings()
