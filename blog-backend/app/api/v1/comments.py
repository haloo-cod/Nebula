"""
通用评论路由 — comments.json 读写
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import require_admin
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentItem, CommentListResponse
from app.services.comment import (
    add_comment,
    delete_comment,
    get_comments_by_page_key,
    get_comment_count,
)

router = APIRouter(prefix="/comments", tags=["评论"])


@router.get("", response_model=CommentListResponse)
async def list_comments(
    page_key: str = Query(..., description="页面标识，如 about / post:slug"),
):
    """获取某页面的评论列表"""
    items = get_comments_by_page_key(page_key)
    return CommentListResponse(items=items, total=len(items))


@router.get("/count")
async def comment_count(
    page_key: str = Query(..., description="页面标识"),
):
    """获取某页面的评论总数（含回复）"""
    count = get_comment_count(page_key)
    return {"page_key": page_key, "count": count}


class BatchCountRequest(BaseModel):
    page_keys: list[str]


@router.post("/batch-count")
async def batch_comment_count(body: BatchCountRequest):
    """批量获取多个页面的评论总数"""
    result: dict[str, int] = {}
    for key in body.page_keys:
        result[key] = get_comment_count(key)
    return result


@router.post("", response_model=CommentItem, status_code=status.HTTP_201_CREATED)
async def create_comment(body: CommentCreate):
    """发表评论（无需认证，后续可加验证码/限流）"""
    comment = add_comment(
        page_key=body.page_key,
        author=body.author,
        content=body.content,
        parent_id=body.parent_id,
    )
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_comment(
    comment_id: int,
    page_key: str = Query(...),
    _: User = Depends(require_admin),
):
    """删除评论（需认证）"""
    success = delete_comment(page_key, comment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
