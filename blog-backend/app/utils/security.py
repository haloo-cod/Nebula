"""
安全工具 — JWT 签发/验证 + 密码哈希
直接使用 bcrypt，不依赖 passlib（passlib 与 Python 3.14+ 的 bcrypt 不兼容）
"""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"


def validate_password_length(password: str) -> str:
    """新密码至少八个字符，且不超过 bcrypt 的七十二字节边界。"""
    if len(password) < 8:
        raise ValueError("密码至少需要 8 个字符")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("密码最多为 72 个 UTF-8 字节")
    return password


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        raise ValueError("密码最多为 72 个 UTF-8 字节")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """超长输入或无效历史哈希按凭据不匹配处理，不截断密码。"""
    encoded = plain.encode("utf-8")
    if len(encoded) > 72:
        return False
    try:
        return bcrypt.checkpw(encoded, hashed.encode("utf-8"))
    except ValueError:
        return False


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


def decode_user_token(token: str, token_type: str = "access") -> dict | None:
    """用户令牌只接受不可复用的 UUID 主体；OAuth state 仍单独解码。"""
    payload = decode_access_token(token)
    if not payload or payload.get("type") != token_type:
        return None
    subject = payload.get("sub")
    if not isinstance(subject, str):
        return None
    try:
        if str(UUID(subject)) != subject:
            return None
    except ValueError:
        return None
    return payload


def create_email_verification_token(auth_id: str, email: str) -> str:
    """创建单次用途由当前邮箱绑定校验的验证令牌。"""

    return create_access_token(
        {"sub": auth_id, "email": email, "type": "email-verification"},
        expires_delta=timedelta(hours=24),
    )
