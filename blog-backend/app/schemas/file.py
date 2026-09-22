"""
通用文件相关 Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel, model_validator

from app.config import settings


def build_r2_url(storage_backend: str, r2_key: str | None) -> str | None:
    """由存储后端与对象键现算 R2 公开直链。

    数据库只存相对路径，直链永远是派生值（域名变更无需刷库）；
    未迁移 / 无对象键 / 未配置自定义域名时返回 None。
    """
    if storage_backend != "r2" or not r2_key or not settings.R2_PUBLIC_DOMAIN:
        return None
    return f"{settings.R2_PUBLIC_DOMAIN.rstrip('/')}/{r2_key}"


class FileResponse(BaseModel):
    """上传文件响应。"""

    id: int
    filename: str
    original_name: str
    url: str
    file_size: int
    mime_type: str
    created_at: datetime
    storage_backend: str = "local"
    r2_key: str | None = None
    r2_url: str | None = None  # R2 直链（仅展示用；local 或未配置域名时为 None）

    @model_validator(mode="after")
    def _derive_r2_url(self) -> "FileResponse":
        """序列化时自动填充 R2 直链，路由层无需手工拼。"""
        if self.r2_url is None:
            self.r2_url = build_r2_url(self.storage_backend, self.r2_key)
        return self

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    """文件分页列表响应。"""

    items: list[FileResponse]
    total: int
