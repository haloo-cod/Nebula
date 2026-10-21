"""
友链相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, TypeAdapter, field_validator


class FriendExchangeInfo(BaseModel):
    """交换友链展示信息。"""

    name: str = ""
    url: str = ""
    avatar: str = ""
    bio: str = ""
    requirements: list[str] = []
    contact: str = ""
    rss_url: str = Field(default="", max_length=2048)

    @field_validator("rss_url", mode="before")
    @classmethod
    def trim_rss_url(cls, value):
        """移除首尾空白，空字符串表示使用本站订阅源。"""
        return value.strip() if isinstance(value, str) else value

    @field_validator("rss_url")
    @classmethod
    def validate_rss_url(cls, value: str) -> str:
        """只接受完整 HTTP(S) 地址，并保留原始路径和查询参数。"""
        if value:
            if not value.lower().startswith(("http://", "https://")) or any(char.isspace() for char in value):
                raise ValueError("RSS 链接必须是完整的 HTTP 或 HTTPS 地址")
            TypeAdapter(HttpUrl).validate_python(value)
        return value


class FriendCreate(BaseModel):
    """创建友链（管理员）"""
    name: str
    bio: str = ""
    avatar: str = ""
    url: str
    sort_order: int = 0


class FriendUpdate(BaseModel):
    """更新友链（管理员）"""
    name: str | None = None
    bio: str | None = None
    avatar: str | None = None
    url: str | None = None
    sort_order: int | None = None


class FriendResponse(BaseModel):
    """友链响应"""
    id: int
    name: str
    bio: str
    avatar: str
    url: str
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FriendListResponse(BaseModel):
    """友链列表响应"""
    items: list[FriendResponse]
    total: int
