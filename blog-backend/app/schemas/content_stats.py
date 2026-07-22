"""主页内容统计响应 schema。"""

from pydantic import BaseModel


class ContentStatsResponse(BaseModel):
    """公开主页展示的内容数量统计。"""

    posts: int
    moments: int
    gallery_projects: int
    active_days: int
