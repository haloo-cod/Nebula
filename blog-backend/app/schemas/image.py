"""
图片相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel


class ImageResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    url: str
    file_size: int
    width: int
    height: int
    mime_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ImageListResponse(BaseModel):
    items: list[ImageResponse]
    total: int
