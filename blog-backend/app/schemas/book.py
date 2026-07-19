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
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookCreate(BaseModel):
    slug: str
    title: str = ""
    author: str = ""
    description: str = ""
    cover_url: str = ""
