"""
背景图相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel, field_validator


class BackgroundCreate(BaseModel):
    """创建背景图记录（管理员）"""
    image_id: int
    theme: str  # 'dark' | 'light'
    device: str  # 'desktop' | 'mobile'
    sort_order: int = 0

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        if v not in ("dark", "light"):
            raise ValueError("theme 必须为 'dark' 或 'light'")
        return v

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        if v not in ("desktop", "mobile"):
            raise ValueError("device 必须为 'desktop' 或 'mobile'")
        return v


class BackgroundResponse(BaseModel):
    """背景图响应"""
    id: int
    url: str  # 图片访问路径（如 /uploads/images/backgrounds/dark-desktop-01.jpg）
    theme: str
    device: str
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BackgroundListResponse(BaseModel):
    """背景图列表响应"""
    items: list[BackgroundResponse]
    total: int


class BackgroundReorderRequest(BaseModel):
    """批量调整排序"""
    ids: list[int]  # 按顺序排列的背景图 ID 列表
