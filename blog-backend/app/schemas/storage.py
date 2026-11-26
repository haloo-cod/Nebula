"""后台目录浏览响应，只描述文件与存储记录，不读取文件正文。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


StorageRoot = Literal["uploads", "content"]


class StorageDirectory(BaseModel):
    """当前目录下的直接子目录。"""

    name: str
    path: str


class StorageFile(BaseModel):
    """合并本地文件与数据库记录后的文件条目。"""

    name: str
    path: str
    title: str = ""
    file_size: int | None = None
    modified_at: datetime | None = None
    local_exists: bool = False
    storage_backend: Literal["local", "r2"] = "local"
    record_kind: str | None = None
    record_id: int | None = None
    r2_key: str | None = None
    r2_url: str | None = None
    url: str | None = None
    manage_url: str | None = None


class StorageBrowseResponse(BaseModel):
    """目录浏览分页结果；目录始终完整返回，文件单独分页。"""

    root: StorageRoot
    path: str
    directories: list[StorageDirectory]
    items: list[StorageFile]
    total: int
    page: int
    page_size: int
    r2_enabled: bool
