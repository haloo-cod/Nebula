"""
展览页相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel


class GalleryBase(BaseModel):
    slug: str = ""
    title: str
    description: str = ""
    tags: list[str] = []
    status: str = ""
    year: str = ""
    is_featured: bool = False


class GalleryCreate(GalleryBase):
    content_md: str = ""


class GalleryUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    year: str | None = None
    is_featured: bool | None = None
    content_md: str | None = None


class GalleryListItem(GalleryBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GalleryDetail(GalleryBase):
    id: int
    content_md: str = ""
    content_html: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
