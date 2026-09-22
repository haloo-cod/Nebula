"""
图片相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel, model_validator

from app.schemas.file import build_r2_url


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
    storage_backend: str = "local"
    r2_key: str | None = None
    r2_url: str | None = None  # R2 直链（仅展示用；local 或未配置域名时为 None）

    @model_validator(mode="after")
    def _derive_r2_url(self) -> "ImageResponse":
        """序列化时自动填充 R2 直链，路由层无需手工拼。"""
        if self.r2_url is None:
            self.r2_url = build_r2_url(self.storage_backend, self.r2_key)
        return self

    model_config = {"from_attributes": True}


class ImageListResponse(BaseModel):
    items: list[ImageResponse]
    total: int
