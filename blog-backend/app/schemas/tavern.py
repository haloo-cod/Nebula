"""
深夜酒馆相关 Pydantic schemas
"""

from datetime import datetime
from pydantic import BaseModel


class TavernPostCreate(BaseModel):
    """发布留言（匿名）"""
    author: str
    topic: str
    body: str


class TavernPostResponse(BaseModel):
    """留言响应"""
    id: int
    author: str
    topic: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TavernPostAdminResponse(BaseModel):
    """管理员视角留言响应（含可见状态）"""
    id: int
    author: str
    topic: str
    body: str
    is_visible: bool
    ip_hash: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TavernListResponse(BaseModel):
    """留言列表响应"""
    items: list[TavernPostResponse]
    total: int


class TavernAdminListResponse(BaseModel):
    """管理员留言列表响应"""
    items: list[TavernPostAdminResponse]
    total: int


class VisibilityUpdate(BaseModel):
    """设置可见/隐藏"""
    is_visible: bool
