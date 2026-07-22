"""
博文相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel


class PostBase(BaseModel):
    slug: str = ""
    title: str
    description: str = ""
    date: str = ""
    cover_url: str = ""
    category: str = ""
    tags: list[str] = []
    is_draft: bool = False
    is_pinned: bool = False


class PostCreate(PostBase):
    """创建博文 — 同时上传 .md 文件内容"""
    content_md: str = ""


class PostUpdate(BaseModel):
    """更新博文元数据"""
    title: str | None = None
    description: str | None = None
    date: str | None = None
    cover_url: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    is_draft: bool | None = None
    is_pinned: bool | None = None
    content_md: str | None = None


class PostListItem(PostBase):
    """列表项（不含正文）"""
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PostDetail(PostBase):
    """详情（含渲染后 HTML + 原文）"""
    id: int
    content_md: str = ""
    content_html: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    items: list[PostListItem]
    total: int


class PostStat(BaseModel):
    label: str
    count: int
