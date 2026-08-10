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

    # ===== 生产配置保护 =====
    ENVIRONMENT: str = "development"

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
    # 开发期局域网预览可临时启用，生产环境不要打开：
    # CORS_ALLOW_ALL: bool = False

    # ===== 管理员初始账户 =====
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"


settings = Settings()


def validate_production_settings() -> None:
    """阻止生产环境使用开发密钥和默认管理员密码。"""
    if settings.ENVIRONMENT.lower() not in {"production", "prod"}:
        return
    invalid = []
    if settings.DEBUG:
        invalid.append("DEBUG 必须为 false")
    if len(settings.SECRET_KEY) < 32 or settings.SECRET_KEY in {"change-me-in-production", "dev-secret-key-change-in-prod"}:
        invalid.append("SECRET_KEY 必须是至少 32 个字符的随机值")
    if settings.ADMIN_PASSWORD in {"admin123", "change-me-in-production"} or len(settings.ADMIN_PASSWORD) < 12:
        invalid.append("ADMIN_PASSWORD 必须是至少 12 个字符的非默认密码")
    if len(settings.ANALYTICS_HASH_SALT) < 32 or settings.ANALYTICS_HASH_SALT == "change-analytics-salt":
        invalid.append("ANALYTICS_HASH_SALT 必须是至少 32 个字符的随机值")
    if not settings.COOKIE_SECURE:
        invalid.append("HTTPS 生产环境必须启用 COOKIE_SECURE")
    if not settings.FRONTEND_URL.startswith("https://"):
        invalid.append("FRONTEND_URL 必须使用 HTTPS")
    if invalid:
        raise RuntimeError("生产配置不安全: " + "; ".join(invalid))
