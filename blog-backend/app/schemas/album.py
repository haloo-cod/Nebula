"""
相册相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel


class PhotoResponse(BaseModel):
    """单张照片响应"""
    id: int
    url: str
    caption: str | None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoCreate(BaseModel):
    """添加照片到相册（管理员）"""
    image_id: int
    caption: str | None = None


class AlbumCreate(BaseModel):
    """创建相册（管理员）"""
    title: str
    description: str = ""
    orientation: str = "portrait"  # 'portrait' | 'landscape'


class AlbumUpdate(BaseModel):
    """更新相册信息（管理员）"""
    title: str | None = None
    description: str | None = None
    orientation: str | None = None
    cover_image_id: int | None = None


class AlbumResponse(BaseModel):
    """相册列表项（含封面 + 照片数量 + 预览图）"""
    id: int
    title: str
    description: str
    orientation: str
    cover_url: str          # 封面 URL：cover_image_id 指定 or 第一张照片
    photo_count: int
    date: str               # 格式化的创建时间 'YYYY.MM'
    created_at: datetime
    preview_photos: list[PhotoResponse]  # 前 3 张照片（卡片堆叠效果用）

    model_config = {"from_attributes": True}


class AlbumDetailResponse(BaseModel):
    """相册详情（含完整照片列表）"""
    id: int
    title: str
    description: str
    orientation: str
    cover_url: str
    photo_count: int
    date: str
    created_at: datetime
    photos: list[PhotoResponse]

    model_config = {"from_attributes": True}


class AlbumListResponse(BaseModel):
    """相册列表响应"""
    items: list[AlbumResponse]
    total: int


class AlbumPhotoReorderRequest(BaseModel):
    """批量调整照片排序"""
    ids: list[int]
