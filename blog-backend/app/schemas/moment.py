"""
说说相关 Pydantic schemas
"""

from pydantic import BaseModel


class MomentCommentResponse(BaseModel):
    id: int
    nickname: str
    content: str
    date: str
    likes: int = 0


class MomentResponse(BaseModel):
    id: int
    date: str
    content: str
    mood: str = ""
    tags: list[str] = []
    images: list[str] = []
    likes: int = 0
    comments: list[MomentCommentResponse] = []


class MomentCreate(BaseModel):
    content: str
    mood: str = ""
    tags: list[str] = []
    images: list[str] = []


class MomentCommentCreate(BaseModel):
    nickname: str
    content: str


class MomentListResponse(BaseModel):
    items: list[MomentResponse]
    total: int
