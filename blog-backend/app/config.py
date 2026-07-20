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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    COOKIE_SECURE: bool = False
    FRONTEND_URL: str = "http://localhost:5173"
    REQUIRE_EMAIL_VERIFICATION: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True

    # ===== GitHub OAuth =====
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_CALLBACK_URL: str = "http://localhost:8000/api/v1/auth/github/callback"
    GITHUB_HTTP_PROXY: str = ""
    GITHUB_HTTP_TIMEOUT: float = 20.0

    # ===== 数据库 =====
    DATABASE_URL: str = "sqlite+aiosqlite:///./blog.db"

    # ===== 文件存储 =====
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    CONTENT_DIR: Path = BASE_DIR / "content"
    DATA_DIR: Path = BASE_DIR / "data"
    TRUST_PROXY_HEADERS: bool = False
    ANALYTICS_ENABLED: bool = True
    ANALYTICS_IP_RETENTION_DAYS: int = 90
    ANALYTICS_HASH_SALT: str = "change-analytics-salt"
    BOOK_ARCHIVE_DIR: Path = UPLOAD_DIR / "book-archives"
    BOOK_ARCHIVE_EXPIRE_HOURS: int = 24 * 7

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
