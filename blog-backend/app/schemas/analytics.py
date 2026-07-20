"""访问统计请求和响应 schemas。"""

from datetime import datetime

from pydantic import BaseModel, Field


class AnalyticsEventCreate(BaseModel):
    """前端上报的行为字段，IP 等请求信息由后端补充。"""

    event_type: str = Field(default="page_view", max_length=40)
    path: str = Field(max_length=500)
    title: str = Field(default="", max_length=300)
    referrer: str = Field(default="", max_length=1000)
    visitor_id: str = Field(default="", max_length=100)


class AnalyticsOverview(BaseModel):
    """访问概览。"""

    today_pv: int
    today_uv: int
    yesterday_pv: int
    yesterday_uv: int
    total_pv: int
    total_uv: int
    page_views: int
    book_downloads: int
    zip_downloads: int


class AnalyticsTrendItem(BaseModel):
    """单日访问趋势。"""

    date: str
    pv: int
    uv: int


class AnalyticsPublicSummary(BaseModel):
    """前台可展示的访问统计聚合数据，不包含访客明细。"""

    today_pv: int
    today_uv: int
    total_pv: int
    total_uv: int
    trend: list[AnalyticsTrendItem]


class AnalyticsPageItem(BaseModel):
    """热门页面统计。"""

    path: str
    title: str
    pv: int
    uv: int


class AnalyticsVisitorItem(BaseModel):
    """管理员可见的最近访客记录。"""

    id: int
    event_type: str
    path: str
    title: str
    ip_address: str
    user_agent: str
    referrer: str
    occurred_at: datetime


class AnalyticsVisitorResponse(BaseModel):
    """最近访客分页响应。"""

    items: list[AnalyticsVisitorItem]
    total: int
