"""
藏宝阁相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel


class TreasureCreate(BaseModel):
    """创建藏宝条目（管理员）"""
    slug: str = ""
    title: str
    description: str = ""
    category: str  # '开源项目' | '工具' | '资源下载'
    icon: str = ""
    url: str = ""
    download_file: str = ""
    tags: list[str] = []
    sort_order: int = 0


class TreasureUpdate(BaseModel):
    """更新藏宝条目（管理员）"""
    title: str | None = None
    description: str | None = None
    category: str | None = None
    icon: str | None = None
    url: str | None = None
    download_file: str | None = None
    tags: list[str] | None = None
    sort_order: int | None = None


class TreasureResponse(BaseModel):
    """藏宝条目响应"""
    id: int
    slug: str
    title: str
    description: str
    category: str
    icon: str
    url: str
    download_file: str
    tags: list[str]
    sort_order: int
    created_at: datetime
    archive_id: int | None = None
    archive_status: str | None = None
    archive_expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class TreasureListResponse(BaseModel):
    """藏宝列表响应"""
    items: list[TreasureResponse]
    total: int
