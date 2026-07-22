"""图书批量下载任务 schemas。"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class BookDownloadJobCreate(BaseModel):
    """创建批量下载任务。"""

    slugs: list[str]
    archive_name: str = "starlit-books"
    expire_days: int = Field(default=7, ge=1, le=3650)


class BookDownloadJobExtend(BaseModel):
    """调整图书归档的到期日期。"""

    expires_on: date


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
    archive_name: str
    expire_days: int
    created_at: datetime


class BookDownloadJobListResponse(BaseModel):
    """批量下载历史分页响应。"""

    items: list[BookDownloadJobResponse]
    total: int
