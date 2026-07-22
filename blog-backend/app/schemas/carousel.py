"""
轮播图相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel


class CarouselSlideCreate(BaseModel):
    """创建轮播图（管理员）"""
    image_id: int
    sort_order: int = 0


class CarouselSlideResponse(BaseModel):
    """轮播图响应"""
    id: int
    url: str  # 图片访问路径
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CarouselListResponse(BaseModel):
    """轮播图列表响应"""
    items: list[CarouselSlideResponse]
    total: int


class CarouselReorderRequest(BaseModel):
    """批量调整排序"""
    ids: list[int]
