"""
通用文件相关 Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel


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

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    """文件分页列表响应。"""

    items: list[FileResponse]
    total: int
