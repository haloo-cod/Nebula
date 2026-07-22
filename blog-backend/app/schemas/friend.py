"""
友链相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel


class FriendExchangeInfo(BaseModel):
    """交换友链展示信息。"""

    name: str = ""
    url: str = ""
    avatar: str = ""
    bio: str = ""
    requirements: list[str] = []
    contact: str = ""


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
