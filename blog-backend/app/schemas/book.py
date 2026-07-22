"""
图书相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel


class BookListItem(BaseModel):
    id: int
    slug: str
    title: str
    author: str
    description: str
    cover_url: str
    file_path: str
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BookListResponse(BaseModel):
    """图书列表响应（含分页）"""
    items: list[BookListItem]
    total: int


class BookDetail(BaseModel):
    id: int
    slug: str
    title: str
    author: str
    description: str
    cover_url: str
    file_path: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookCreate(BaseModel):
    slug: str
    title: str = ""
    author: str = ""
    description: str = ""
    cover_url: str = ""


class BookUpdate(BaseModel):
    """管理员手动更新图书元数据与封面。"""

    title: str | None = None
    author: str | None = None
    description: str | None = None
    cover_url: str | None = None
    sort_order: int | None = None


class BookReorderRequest(BaseModel):
    """按给定 slug 顺序重排全部图书。"""

    slugs: list[str]


class BookCoverCandidate(BaseModel):
    """EPUB 内可供管理员选择的封面图片。"""

    item_name: str
    filename: str
    media_type: str
    width: int
    height: int
    size: int
    score: float
    recommended: bool
    preview_data_url: str


class BookCoverSelection(BaseModel):
    """管理员选择的 EPUB manifest 图片。"""

    item_name: str
