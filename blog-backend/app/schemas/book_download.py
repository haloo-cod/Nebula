"""图书批量下载任务 schemas。"""

from datetime import datetime

from pydantic import BaseModel


class BookDownloadJobCreate(BaseModel):
    """创建批量下载任务。"""

    slugs: list[str]


class BookDownloadJobResponse(BaseModel):
    """批量下载任务状态。"""

    id: int
    status: str
    total_books: int
    completed_books: int
    progress: int
    file_size: int
    error_message: str
    expires_at: datetime | None
    download_url: str | None
    created_at: datetime


class BookDownloadJobListResponse(BaseModel):
    """批量下载历史分页响应。"""

    items: list[BookDownloadJobResponse]
    total: int
