"""
背景图相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, TypeAdapter, field_validator


class BackgroundSourceUpdate(BaseModel):
    """背景来源字段，创建和编辑共用校验。编辑时必须同时提交两项。"""
    source_text: str = Field(max_length=120)
    source_url: str = Field(max_length=2048)

    @field_validator("source_text", "source_url", mode="before")
    @classmethod
    def trim_source(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str) -> str:
        if value:
            if not value.lower().startswith(("http://", "https://")) or any(char.isspace() for char in value):
                raise ValueError("来源链接必须是完整的 HTTP 或 HTTPS 地址")
            # 只校验完整 HTTP(S) 地址，保留用户填写的路径与参数。
            TypeAdapter(HttpUrl).validate_python(value)
        return value


class BackgroundCreate(BackgroundSourceUpdate):
    """创建背景图记录（管理员）"""
    image_id: int | None = None
    media_type: str = "image"
    media_url: str = ""
    poster_url: str = ""
    mime_type: str = ""
    file_size: int = 0
    theme: str  # 'dark' | 'light'
    device: str  # 'desktop' | 'mobile'
    sort_order: int = 0
    source_text: str = Field(default="", max_length=120)
    source_url: str = Field(default="", max_length=2048)

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

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, v: str) -> str:
        if v not in ("image", "video"):
            raise ValueError("media_type must be image or video")
        return v


class BackgroundResponse(BaseModel):
    """背景图响应"""
    id: int
    media_type: str = "image"
    poster_url: str = ""
    mime_type: str = ""
    file_size: int = 0
    source_text: str = ""
    source_url: str = ""
    url: str  # 图片访问路径（如 /uploads/images/backgrounds/dark-desktop-01.jpg）
    theme: str
    device: str
    sort_order: int
    created_at: datetime
    storage_backend: str = "local"  # 视频背景的存储后端（R2 迁移面板用）

    model_config = {"from_attributes": True}


class BackgroundListResponse(BaseModel):
    """背景图列表响应"""
    items: list[BackgroundResponse]
    total: int


class BackgroundReorderRequest(BaseModel):
    """批量调整同一主题和设备分组的排序。"""
    ids: list[int]  # 按顺序排列的背景图 ID 列表
    theme: str
    device: str

    @field_validator("theme")
    @classmethod
    def validate_theme_for_reorder(cls, v: str) -> str:
        if v not in ("dark", "light"):
            raise ValueError("theme 必须为 'dark' 或 'light'")
        return v

    @field_validator("device")
    @classmethod
    def validate_device_for_reorder(cls, v: str) -> str:
        if v not in ("desktop", "mobile"):
            raise ValueError("device 必须为 'desktop' 或 'mobile'")
        return v
