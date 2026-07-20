"""访问统计辅助函数。"""

import hashlib
from datetime import datetime, timezone

from fastapi import Request

from app.config import settings


def get_client_ip(request: Request) -> str:
    """按安全顺序读取客户端 IP，默认不信任可伪造的代理头。"""
    if settings.TRUST_PROXY_HEADERS:
        cloudflare_ip = request.headers.get("CF-Connecting-IP")
        if cloudflare_ip:
            return cloudflare_ip.strip()[:80]
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()[:80]
    return (request.client.host if request.client else "")[:80]


def hash_ip(ip_address: str) -> str:
    """使用配置盐生成不可逆 IP 哈希。"""
    return hashlib.sha256(f"{settings.ANALYTICS_HASH_SALT}:{ip_address}".encode()).hexdigest()


def utc_now() -> datetime:
    """返回带 UTC 时区的当前时间。"""
    return datetime.now(timezone.utc)
