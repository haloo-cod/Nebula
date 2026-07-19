"""
个人资料相关 Pydantic schemas
"""

from pydantic import BaseModel


class SocialLinkResponse(BaseModel):
    """社交链接响应"""
    id: int
    label: str
    icon: str
    url: str
    sort_order: int

    model_config = {"from_attributes": True}


class SocialLinkCreate(BaseModel):
    """创建社交链接"""
    label: str
    icon: str
    url: str
    sort_order: int = 0


class ProfileResponse(BaseModel):
    """个人资料响应"""
    name: str
    bio: str
    avatar_url: str
    cover_url: str
    social_links: list[SocialLinkResponse]

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    """更新个人资料"""
    name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    cover_url: str | None = None
