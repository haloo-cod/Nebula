"""
评论相关 Pydantic schemas
"""

from pydantic import BaseModel


class CommentItem(BaseModel):
    id: int
    author: str
    date: str
    content: str
    avatar_color: str = ""
    children: list["CommentItem"] = []


class CommentCreate(BaseModel):
    page_key: str
    author: str
    content: str
    parent_id: int | None = None


class CommentListResponse(BaseModel):
    items: list[CommentItem]
    total: int
