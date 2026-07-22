"""评论相关 Pydantic schemas。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CommentItem(BaseModel):
    """账户评论及历史匿名评论响应。"""

    id: int
    user_id: int | None = None
    author: str
    date: str
    content: str
    avatar_url: str = ""
    avatar_color: str = ""
    can_delete: bool = False
    children: list["CommentItem"] = Field(default_factory=list)


class CommentCreate(BaseModel):
    """登录用户发表评论请求。"""

    page_key: str
    content: str
    parent_id: int | None = None

    @field_validator("page_key")
    @classmethod
    def validate_page_key(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 300:
            raise ValueError("页面标识不正确")
        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not 1 <= len(value) <= 2000:
            raise ValueError("评论内容需为 1-2000 个字符")
        return value


class CommentListResponse(BaseModel):
    """评论树列表。"""

    items: list[CommentItem]
    total: int
