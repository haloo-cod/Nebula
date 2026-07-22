"""
安全工具 — JWT 签发/验证 + 密码哈希
直接使用 bcrypt，不依赖 passlib（passlib 与 Python 3.14+ 的 bcrypt 不兼容）
"""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import bcrypt
from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    # 访问令牌必须带有明确类型，避免其他用途的 JWT 被当作登录凭证。
    to_encode.setdefault("type", "access")
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token() -> str:
    """生成只发送给客户端一次的高熵刷新令牌。"""

    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """对刷新令牌做不可逆摘要后再存入数据库。"""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_email_verification_token(user_id: int, email: str) -> str:
    """创建单次用途由当前邮箱绑定校验的验证令牌。"""

    return create_access_token(
        {"sub": str(user_id), "email": email, "type": "email-verification"},
        expires_delta=timedelta(hours=24),
    )
