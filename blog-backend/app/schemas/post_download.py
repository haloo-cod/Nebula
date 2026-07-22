"""文章批量下载任务 schema。"""

from datetime import datetime

from pydantic import BaseModel, Field


class PostDownloadJobCreate(BaseModel):
    """创建文章 ZIP 任务。"""

    slugs: list[str] = Field(min_length=1, max_length=100)
    archive_name: str = "starlit-posts"
    include_images: bool = False


class PostDownloadJobResponse(BaseModel):
    """文章 ZIP 任务状态。"""

    id: int
    status: str
    total_posts: int
    completed_posts: int
    progress: int
    error_message: str
    download_url: str | None
    created_at: datetime | None
